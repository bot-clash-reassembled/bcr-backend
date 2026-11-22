import functools
import json
from pathlib import Path
from typing import List

from anyio.to_thread import run_sync


@functools.cache
def _get_design_templates_registry() -> List[dict]:
    file_path = Path(__file__).parent / "design-templates-registry.json"
    with open(file_path, "r") as f:
        return json.load(f)


class DesignTemplateService:
    async def list_design_templates(self):
        return await run_sync(_get_design_templates_registry)
