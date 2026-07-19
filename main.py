"""Entry point for Railway deployment — starts the demo fixture API."""
import os
import uvicorn
from scripts.demo_api import app  # noqa: F401 (re-exported for uvicorn)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
