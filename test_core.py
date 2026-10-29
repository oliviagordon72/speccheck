import json
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

import core
from app import Handler, ThreadingHTTPServer
from core import Claim, Draft, Passage, Review, ReviewBatch


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pdf = (core.ROOT / 'sample' / 'SC100_Fictional_Datasheet.pdf').read_bytes()
        cls.passages = core.parse_pdf(cls.pdf)

    def test_all_sample_fixtures(self):
        expected = {'wrong-limit':'contradicted','within-range':'supported',
                    'wrong-unit':'contradicted','missing-evidence':'insufficient_evidence'}
        for key, verdict in expected.items():
            with self.subTest(key=key):
                result = core.demo_review(key,self.passages)
                self.assertEqual(result['reviews'][0]['verdict'],verdict)
                self.assertEqual(result['mode'],'sample_rules')
                self.assertEqual(result['calls'],[])
                self.assertTrue(result['reviews'][0]['evidence_ids'])

    def test_pdf_provenance(self):
        self.assertEqual({p.page for p in self.passages},{1,2})
        self.assertEqual(len({p.id for p in self.passages}),len(self.passages))
        self.assertTrue(any(p.kind=='table' for p in self.passages))

    def test_invalid_pdf_rejected(self):
        with self.assertRaisesRegex(ValueError,'PDF'):
            core.parse_pdf(b'not a PDF')

    def test_oversize_rejected(self):
        with self.assertRaisesRegex(ValueError,'12 MB'):
            core.checked_pdf(b'%PDF-'+b'x'*(12*1024*1024))

    def test_endpoint_constraints(self):
        for url in ['http://a.openai.azure.com','https://example.com',
                    'https://a.openai.azure.com.evil.com','https://user:pass@a.openai.azure.com',
                    'https://a.openai.azure.com/openai/v1','https://a.openai.azure.com?x=1']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                core.azure_endpoint(url,'ai')
        self.assertEqual(core.azure_endpoint('https://example.openai.azure.com/','ai'),
                         'https://example.openai.azure.com')

    def test_azure_cells_and_footnotes_preserved(self):
        result={'paragraphs':[{'content':'Valid only at 25 C','role':'footnote',
                    'boundingRegions':[{'pageNumber':2,'polygon':[0,0,1,1]}]}],
                'tables':[{'boundingRegions':[{'pageNumber':2}], 'cells':[
                    {'rowIndex':0,'columnIndex':0,'kind':'columnHeader','columnSpan':2,'content':'Typical'},
                    {'rowIndex':1,'columnIndex':0,'content':'30 mA'}]}]}
        p=core.azure_passages(result)
        self.assertEqual(p[0].kind,'footnote')
        self.assertEqual(p[0].page,2)
        self.assertIn('columnSpan=2',p[1].text)
        self.assertIn('30 mA',p[1].text)

    def test_missing_citation_cannot_be_supported(self):
        d=Draft(answer='yes',claims=[Claim(text='yes',evidence_ids=['invented'])])
        b=ReviewBatch(reviews=[Review(claim_index=0,verdict='supported',evidence_ids=['invented'],explanation='yes')])
        rows=core.finalize(d,b,self.passages)
        self.assertEqual(rows[0]['verdict'],'insufficient_evidence')
        self.assertEqual(rows[0]['invalid_citations'],['invented'])

    def test_no_evidence_cannot_establish_contradiction(self):
        d=Draft(answer='yes',claims=[Claim(text='yes',evidence_ids=[])])
        b=ReviewBatch(reviews=[Review(claim_index=0,verdict='contradicted',evidence_ids=[],explanation='no')])
        self.assertEqual(core.finalize(d,b,self.passages)[0]['verdict'],'insufficient_evidence')

    def test_omitted_and_duplicate_claims_rejected(self):
        d=Draft(answer='yes',claims=[Claim(text='yes',evidence_ids=[])])
        r=Review(claim_index=0,verdict='insufficient_evidence',evidence_ids=[],explanation='unknown')
        for reviews in [[],[r,r]]:
            with self.assertRaises(ValueError):
                core.finalize(d,ReviewBatch(reviews=reviews),self.passages)

    def test_live_review_uses_full_context_and_original_answer(self):
        d=Draft(answer='silently changed',claims=[Claim(text='original claim',evidence_ids=['p1-l8'])])
        b=ReviewBatch(reviews=[Review(claim_index=0,verdict='contradicted',evidence_ids=['p1-l8'],explanation='wrong operating limit')])
        responses=[(d,{'model':'fake','usage':{}}),(b,{'model':'fake','usage':{}})]
        with patch('core.model_call',side_effect=responses) as call:
            result=core.live_review(self.passages,'Can it operate at 100 C?',{},'Original answer')
        self.assertEqual(result['answer'],'Original answer')
        review_input=json.loads(call.call_args_list[1].args[2])
        self.assertIn('p2-',review_input['all_sources'])
        self.assertEqual(len(result['calls']),2)

    def test_provider_payload_and_response_parse(self):
        captured=[]
        def fake_request(url,**kwargs):
            captured.append((url,json.loads(kwargs['data'])))
            return {'model':'fake','output':[{'content':[{'type':'output_text',
                'text':json.dumps({'answer':'Unknown','claims':[]})}]}]},{}
        with patch('core.request',side_effect=fake_request):
            output,_=core.model_call({'ai_key':'fake-key','model':'fake'},'instructions','question',Draft)
        self.assertEqual(output.answer,'Unknown')
        self.assertFalse(captured[0][1]['store'])
        self.assertTrue(captured[0][1]['text']['format']['strict'])
        self.assertEqual(captured[0][0],'https://api.openai.com/v1/responses')


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()

    def post(self,path,payload,origin=None):
        headers={'Content-Type':'application/json'}
        if origin: headers['Origin']=origin
        req=urllib.request.Request(self.base+path,data=json.dumps(payload).encode(),headers=headers)
        return urllib.request.urlopen(req)

    def test_page_and_sample_review(self):
        with urllib.request.urlopen(self.base) as r:
            self.assertIn(b'Evidence before confidence',r.read())
        with self.post('/api/sample',{}) as r:
            document=json.load(r)
        with self.post('/api/review',{'document_id':document['document_id'],'mode':'sample','scenario':'wrong-limit'}) as r:
            report=json.load(r)
        self.assertEqual(report['reviews'][0]['verdict'],'contradicted')
        self.assertNotIn('config',report)
        self.assertEqual(len(report['document']['sha256']),64)

    def test_cross_origin_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.post('/api/sample',{},origin='https://unrelated.example')
        self.assertEqual(ctx.exception.code,403)

    def test_missing_document_handled(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.post('/api/review',{'document_id':'missing'})
        self.assertEqual(ctx.exception.code,400)


if __name__=='__main__':
    unittest.main(verbosity=2)
