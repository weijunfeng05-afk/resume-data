"""Manual connection check; sends no resume content."""
import sys
from pathlib import Path
import os
from dotenv import load_dotenv
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from screening import test_deepseek_connection, DEFAULT_DEEPSEEK_BASE_URL, DEFAULT_DEEPSEEK_MODEL

def main():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    try:
        reply = test_deepseek_connection(
            os.getenv("DEEPSEEK_API_KEY", ""),
            os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL),
            os.getenv("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL),
        )
    except Exception as exc:
        print(f"Connection failed: {type(exc).__name__}")
        return 1
    print(reply)
    return 0

if __name__ == "__main__":
    sys.exit(main())
