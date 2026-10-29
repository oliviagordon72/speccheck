"""Check four hand-written fixtures. This is not an AI accuracy benchmark."""
import json
from core import ROOT, SCENARIOS, demo_review, parse_pdf

expected={'wrong-limit':'contradicted','within-range':'supported',
          'wrong-unit':'contradicted','missing-evidence':'insufficient_evidence'}
passages=parse_pdf((ROOT/'sample'/'SC100_Fictional_Datasheet.pdf').read_bytes())
rows=[]
for scenario in SCENARIOS:
    result=demo_review(scenario,passages)
    actual=result['reviews'][0]['verdict']
    rows.append({'scenario':scenario,'expected':expected[scenario],'actual':actual,'passed':actual==expected[scenario]})
print(json.dumps({'type':'hand-written sample fixture checks; no model calls', 'checks':rows},indent=2))
raise SystemExit(0 if all(r['passed'] for r in rows) else 1)
