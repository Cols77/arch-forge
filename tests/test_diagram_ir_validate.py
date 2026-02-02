from __future__ import annotations

import pytest

from tourassist.app import config
from tourassist.app.diagram_ir.io import load_ir, save_ir
from tourassist.app.diagram_ir.validate import edges_for_compilation
from tourassist.app.diagram_ir.validate import IRValidationError, validate_ir_dict


def _valid_ir_dict() -> dict:
    return {
        "version": "1.0",
        "generated_at": "2026-01-31T00:00:00Z",
        "nodes": [
            {
                "id": "svc.ingest",
                "label": "Ingestion API",
                "type": "service",
                "status": "implemented",
                "provenance": {
                    "kind": "code",
                    "file": "app/api/ingest.py",
                    "line_start": 1,
                    "line_end": 10,
                    "symbol": "ingest_file",
                },
            }
        ],
        "edges": [
            {
                "from": "svc.ingest",
                "to": "svc.ingest",
                "type": "calls",
                "status": "implemented",
                "provenance": {
                    "kind": "markdown",
                    "file": "docs/architecture.md",
                    "heading": "Ingestion Pipeline",
                    "line_start": 42,
                    "line_end": 88,
                },
            }
        ],
    }


def test_validate_ir_dict_valid_ir_passes() -> None:
    ir = validate_ir_dict(_valid_ir_dict())
    assert ir.version == "1.0"
    assert len(ir.nodes) == 1
    assert len(ir.edges) == 1


def test_ir_load_save_round_trip(tmp_path) -> None:
    ir = validate_ir_dict(_valid_ir_dict())
    path = tmp_path / "ir.json"
    save_ir(ir, path)
    loaded = load_ir(path)
    assert loaded.model_dump() == ir.model_dump()


def test_ir_written_to_configured_location_smoke() -> None:
    ir = validate_ir_dict(_valid_ir_dict())
    save_ir(ir, config.settings.diagram_ir_path)
    assert config.settings.diagram_ir_path.exists()


@pytest.mark.parametrize(
    ("mutate", "expected_substring"),
    [
        (lambda d: d.pop("nodes"), "nodes: Field required"),
        (lambda d: d["nodes"][0].__setitem__("status", "nope"), "nodes.0.status"),
    ],
)
def test_validate_ir_dict_schema_errors_raise_actionable_messages(mutate, expected_substring) -> None:
    data = _valid_ir_dict()
    mutate(data)
    with pytest.raises(IRValidationError) as exc:
        validate_ir_dict(data)
    assert expected_substring in str(exc.value)


def test_validate_ir_dict_malformed_provenance_fails() -> None:
    data = _valid_ir_dict()
    data["nodes"][0]["provenance"] = {
        "kind": "code",
        "file": "app/main.py",
        "line_start": 10,
        "line_end": 1,
        "symbol": "main",
    }
    with pytest.raises(IRValidationError) as exc:
        validate_ir_dict(data)
    assert "line_end must be" in str(exc.value)


def test_validate_ir_dict_code_provenance_requires_symbol_or_callsite() -> None:
    data = _valid_ir_dict()
    data["nodes"][0]["provenance"] = {
        "kind": "code",
        "file": "app/main.py",
        "line_start": 1,
        "line_end": 2,
    }
    with pytest.raises(IRValidationError) as exc:
        validate_ir_dict(data)
    assert "requires 'symbol' or 'callsite'" in str(exc.value)


def test_validate_ir_dict_missing_line_range_fails() -> None:
    data = _valid_ir_dict()
    data["nodes"][0]["provenance"].pop("line_end")
    with pytest.raises(IRValidationError) as exc:
        validate_ir_dict(data)
    assert "line_end: Field required" in str(exc.value)


def test_validate_ir_dict_rejects_blank_provenance_file() -> None:
    data = _valid_ir_dict()
    data["nodes"][0]["provenance"]["file"] = "   "
    with pytest.raises(IRValidationError) as exc:
        validate_ir_dict(data)
    assert "nodes.0.provenance.file: must be non-empty" in str(exc.value)


def test_validate_ir_dict_rejects_dangling_edge_refs() -> None:
    data = _valid_ir_dict()
    data["edges"][0]["to"] = "missing.node"
    with pytest.raises(IRValidationError) as exc:
        validate_ir_dict(data)
    assert "edges.0.to: unknown node id 'missing.node'" in str(exc.value)


def test_edges_for_compilation_omits_unknown() -> None:
    data = _valid_ir_dict()
    data["edges"].append(
        {
            "from": "svc.ingest",
            "to": "svc.ingest",
            "type": "calls",
            "status": "unknown",
            "provenance": {
                "kind": "markdown",
                "file": "docs/architecture.md",
                "heading": "Ingestion Pipeline",
                "line_start": 90,
                "line_end": 100,
            },
        }
    )
    ir = validate_ir_dict(data)
    assert len(ir.edges) == 2
    assert len(edges_for_compilation(ir)) == 1
