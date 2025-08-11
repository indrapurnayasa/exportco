import os
import asyncio

from dotenv import load_dotenv

# Ensure project root is on path when running directly
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv()

from app.db.database import AsyncSessionLocal  # noqa: E402
from app.services.prompt_library_service import PromptLibraryService  # noqa: E402


async def main():
    # Require API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY is not set in environment.")
        return 1

    force = os.getenv("FORCE_REEMBED", "false").lower() in ("1", "true", "yes")

    async with AsyncSessionLocal() as session:
        service = PromptLibraryService(session)
        updated = await service.backfill_embeddings(model="text-embedding-3-small", force=force)
        print(f"Re-embedded prompts: {updated} updated. Force={force}")
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))


