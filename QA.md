# Build verification

- 14 automated unittest tests passed in the build environment.
- All four hand-written sample fixture checks passed against the actual bundled PDF.
- Inline JavaScript passed `node --check`.
- The two-page fictional datasheet was rendered and visually inspected.
- HTTP route tests exercised the page, sample loading, review response, missing-document errors, and cross-origin rejection through an actual local test server.
- Cloud request construction and response parsing were tested with a mock transport.

Not verified:

- Browser interaction: the managed preview launcher could not find a Python executable and did not launch the Python application. No browser interaction test was completed.
- Real Azure Document Intelligence or AI provider calls: no provider credentials were configured in the build environment.
- Model correctness, comparative extraction accuracy, latency, or cost: a human-labeled live evaluation has not been run.
- Windows launcher: supplied for convenience, not executed in this Linux build environment.

The sample rule checks are not evidence of AI accuracy. Run a live request with your credentials before relying on live mode for an interview demonstration.
