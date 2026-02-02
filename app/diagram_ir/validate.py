from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from tourassist.app.diagram_ir.schema import IRDocument, IREdge, IRStatus


@dataclass(frozen=True)
class IRValidationError(Exception):
    errors: tuple[str, ...]

    def __str__(self) -> str:
        return "\n".join(self.errors)


def edges_for_compilation(ir: IRDocument) -> list[IREdge]:
    return [edge for edge in ir.edges if edge.status != IRStatus.unknown]


def validate_ir_dict(data: Any, *, source: str | None = None) -> IRDocument:
    try:
        ir = IRDocument.model_validate(data)
    except ValidationError as exc:
        prefix = f"{source}: " if source else ""
        errors = []
        for err in exc.errors():
            loc = ".".join(str(part) for part in err.get("loc", ()))
            msg = err.get("msg", "invalid")
            errors.append(f"{prefix}{loc}: {msg}")
        raise IRValidationError(tuple(errors)) from None

    errors = _validate_semantics(ir)
    if errors:
        prefix = f"{source}: " if source else ""
        raise IRValidationError(tuple(f"{prefix}{e}" for e in errors))
    return ir


def _validate_semantics(ir: IRDocument) -> list[str]:
    errors: list[str] = []
    node_ids = [node.id for node in ir.nodes]
    node_id_set = set(node_ids)

    dupes = _find_duplicates(node_ids)
    for dupe in dupes:
        errors.append(f"nodes: duplicate id '{dupe}'")

    for idx, node in enumerate(ir.nodes):
        errors.extend(_validate_provenance(f"nodes.{idx}.provenance", node.provenance))

    for idx, edge in enumerate(ir.edges):
        if edge.from_id not in node_id_set:
            errors.append(f"edges.{idx}.from: unknown node id '{edge.from_id}'")
        if edge.to_id not in node_id_set:
            errors.append(f"edges.{idx}.to: unknown node id '{edge.to_id}'")
        errors.extend(_validate_provenance(f"edges.{idx}.provenance", edge.provenance))

    return errors


def _validate_provenance(prefix: str, provenance: Any) -> list[str]:
    errors: list[str] = []
    file_path = getattr(provenance, "file", "")
    if not str(file_path).strip():
        errors.append(f"{prefix}.file: must be non-empty")
    line_start = getattr(provenance, "line_start", None)
    line_end = getattr(provenance, "line_end", None)
    if line_start is None:
        errors.append(f"{prefix}.line_start: missing")
    if line_end is None:
        errors.append(f"{prefix}.line_end: missing")

    kind = getattr(provenance, "kind", None)
    if kind == "markdown":
        heading = getattr(provenance, "heading", "")
        if not str(heading).strip():
            errors.append(f"{prefix}.heading: must be non-empty")
    if kind == "code":
        symbol = str(getattr(provenance, "symbol", "") or "").strip()
        callsite = str(getattr(provenance, "callsite", "") or "").strip()
        if not symbol and not callsite:
            errors.append(f"{prefix}: code provenance requires 'symbol' or 'callsite'")
    return errors


def _find_duplicates(items: list[str]) -> set[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for item in items:
        if item in seen:
            dupes.add(item)
        seen.add(item)
    return dupes
