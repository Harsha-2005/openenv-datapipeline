"""
server/app.py — OpenEnv entry point required by openenv validate.
Exposes main() function and if __name__ == '__main__' block.
"""
import sys
import os

# Add project root to path so all packages are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from app import app


def main():
    """Main entry point — starts the OpenEnv Data Pipeline Debugger server."""
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1,
    )


if __name__ == "__main__":
    main()
