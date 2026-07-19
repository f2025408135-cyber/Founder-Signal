"""Seed the default Maschmeyer Group thesis.

Usage:
    python scripts/seed_thesis.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from scripts.seed_fixtures import seed_thesis


async def main():
    tid = await seed_thesis()
    print(f"Active thesis id: {tid}")


if __name__ == "__main__":
    asyncio.run(main())
