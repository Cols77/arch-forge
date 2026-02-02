from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tourassist.app.diagram_ir.schema import IRDocument
from tourassist.app.diagram_ir.validate import validate_ir_dict


def load_ir(path: Path) -> IRDocument:
    data = json.loads(path.read_text(encoding="utf-8"))
    return validate_ir_dict(data, source=str(path))


def save_ir(ir: IRDocument, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: Any = ir.model_dump(mode="json", by_alias=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

