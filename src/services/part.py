import functools
import json
from pathlib import Path
from typing import List

from anyio.to_thread import run_sync


@functools.cache
def _get_parts_registry() -> List[dict]:
    file_path = Path(__file__).parent / "parts-registry.json"
    with open(file_path, "r") as f:
        return json.load(f)


class PartService:
    async def list_parts(self):
        return await run_sync(_get_parts_registry)
