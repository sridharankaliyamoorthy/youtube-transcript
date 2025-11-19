Perplexity (Sona) integration
=================================

This project includes an optional integration with Perplexity's Sona summarization API.

Configuration
- Do NOT store your API key in the repository. Set the `PPLX_API_KEY` environment variable in your shell before starting the server.

Example (zsh):

```bash
export PPLX_API_KEY="<your-perplexity-api-key>"
uvicorn scripts.api_app:app --reload
```

If the Perplexity endpoint differs from the default, set `PPLX_API_URL`.

Testing without network
- When running the test harness locally, the test code monkeypatches the Perplexity call so you don't need a live key or network.
