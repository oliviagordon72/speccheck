# SpecCheck 0.1

A runnable first version of evidence review for engineering documents.

## Start today

Requires Python 3.10 or newer. On Windows, you can double-click **START_WINDOWS.bat** to create a local virtual environment, install dependencies, and launch the app. The launcher has not been executed in this Linux build environment.

Alternatively, extract this folder, open a terminal in it, then run:

```bash
python -m pip install -r requirements.txt
python app.py
```

On Windows, use `py` in place of `python` if that is your Python launcher.
Open **http://127.0.0.1:3000** in your browser. Stop with Ctrl+C.
If port 3000 is occupied, run `python app.py --port 3001`.

The sample walkthrough works without API credentials. Select a case and click **Run sample check**. It uses hand-written answers and actual numerical rules against the bundled fictional PDF. It does not call an AI model or estimate model accuracy.

## Make it a live AI demo

1. Open **Settings**.
2. Choose **OpenAI API** or **Azure OpenAI**.
3. Enter your API key and a model supporting the Responses API with strict structured outputs. For Azure, also enter your resource root endpoint and the deployment name. The suggested OpenAI model is editable.
4. Choose **Live AI review**. Keep the sample PDF or upload your own text-based PDF.
5. Ask a question and click **Run live AI review**. Or select **Review an existing answer**, paste an intentionally flawed answer, and have the model review its claims.
6. Inspect each verdict and source link; export the review JSON.

For a reliable demonstration of a wrong answer, paste the flawed answer yourself. A live generator may correctly answer the question and should not be forced to hallucinate.

Azure Document Intelligence and Azure OpenAI are separate services and require their respective credentials. You can use local PDF extraction with either AI provider.

### Azure document extraction

In Settings, enter the Document Intelligence resource root endpoint and key. In Live mode, choose **Azure Document Intelligence · Layout**, select a PDF, and click **Extract selected PDF**. The adapter uses `prebuilt-layout` with API version `2024-11-30`. It preserves paragraphs, table cell indices, spans, and bounding regions in the raw extraction export, including nearby paragraphs such as footnotes.

Supported root examples:

- Document extraction: `https://your-resource.cognitiveservices.azure.com`
- Azure AI: `https://your-resource.openai.azure.com`

Use root endpoints without API paths. Custom proxy domains and sovereign-cloud endpoints are outside this prototype's supported endpoint allowlist.

### Optional server environment variables

Instead of entering keys in the interface, configure the server environment before launching:

- `OPENAI_API_KEY`, optional `OPENAI_MODEL`
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_DOCUMENT_INTELLIGENCE_KEY`, `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`

The app does not read a `.env` file automatically. UI settings take precedence. Keep credentials out of source files, exports, and screenshots.

## Two-minute walkthrough

1. Open the sample walkthrough and select **Storage is not operation**.
2. Show the hand-written answer that incorrectly applies 125°C to operation.
3. Run the sample check. Open the cited passage and the original PDF.
4. Select **A supported specification** to show that a valid answer passes.
5. Select **A thousandfold unit error** to demonstrate the 30 mA / 30 A mismatch.
6. Select **Know when to stop** to demonstrate insufficient evidence.
7. If credentials are configured, move to Live AI review, paste the flawed temperature answer, and show a real model assessment. Clearly distinguish this from the sample rule checks.

## Implemented

- PDF upload with local `pdfplumber` extraction.
- Azure Document Intelligence Layout REST adapter with bounded polling.
- Two structured Responses API calls: initial answer/claim extraction, then an evidence review.
- Keyword-based initial retrieval with adjacent passages. The reviewer gets the full bounded extracted document so it can inspect context the first call missed.
- Pydantic schemas for claims and verdicts; deterministic checks for missing or invalid citation IDs and incomplete claim coverage.
- Three claim verdicts and source-linked explanations.
- Original PDF view, extraction export, review export, document SHA-256, model IDs, usage, and timing.
- Four clearly labeled sample fixtures with actual local numerical checks.

The initial UI is a lightweight HTML interface served by Python's standard library. There is no frontend build or Streamlit installation. Evaluation currently uses a small unittest suite and fixture runner; Inspect integration and model benchmark comparisons remain future work.

## Verification performed in this build

Run:

```bash
python -m unittest -v
python evaluate_samples.py
```

Tests exercise the sample PDF, fixture verdicts, citation failures, missing/duplicate claim reviews, Azure result normalization, provider request/response shape using a mock transport, source context, and HTTP routes.

**Live provider calls require your credentials and have not been tested against a real Azure or OpenAI resource in this environment.** Mock transport tests verify adapter shape, not cloud compatibility, permissions, available deployments, OCR quality, model quality, or latency. The four sample cases are not an AI evaluation dataset or accuracy claim.

## Deliberate limits

- 20 pages, 12 MB per PDF; extracted live-review context capped at 90,000 characters. Oversize context is rejected rather than silently truncated.
- Local extraction does not OCR scanned PDFs; use Azure Layout for those.
- Table parsing and model assessments can be wrong. Inspect the original PDF when a condition depends on layout.
- Citation checks establish that identifiers exist. They do not establish semantic support; the live review step is model judgment.
- Live numeric and unit reasoning is model-based in this version. Deterministic numerical checks are implemented only for the four sample scenarios.
- No overall safety approval, production authentication, persistent database, automatic corrections, or actions based on answers.
- Uploaded documents are held in bounded server memory. Reset or restart to clear the selected document/session state; restarting clears server memory. API keys are read for each request, not saved to disk or exports. Extracted text is sent to your selected model provider in live mode, and PDFs are sent to Azure when Azure extraction is selected.
- This is a local development server, bound to loopback by default. Do not expose it publicly as a production service.

## Next experiment

Build a human-labeled set of approximately 24 questions. Freeze initial answers and compare citation-only, self-check, and separate-review workflows. Record unsupported claims accepted, correct claims rejected, useful answer coverage, and added latency. Keep test documents separate from prompt development for a larger follow-up study.

## Primary API references

- https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/layout
- https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/responses
- https://developers.openai.com/api/docs/guides/structured-outputs
- https://github.com/jsvine/pdfplumber

## Interview use

Discuss only completed work and real observations. The cloud adapters, rule-based sample mode, and model-based live mode are distinct. Report actual measured results after running a labeled evaluation; do not describe fixture checks as evidence of AI accuracy.
