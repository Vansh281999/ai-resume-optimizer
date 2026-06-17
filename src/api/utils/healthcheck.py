import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ai_career_platform.config import settings


def main() -> int:
    key = settings.OPENAI_API_KEY
    print(f"OPENAI_API_KEY present: {bool(key)}")
    if not key:
        print("AI provider: not configured (fallback mode)")
        return 0
    print(f"Key prefix: {key[:4]}****")
    print("AI provider: configured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
