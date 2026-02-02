from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class IRStatus(str, Enum):
    implemented = "implemented"
    spec_only = "spec_only"
    inferred = "inferred"
    unknown = "unknown"


class ProvenanceBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file: str = Field(min_length=1)
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)

    @model_validator(mode="after")
    def _validate_line_range(self) -> "ProvenanceBase":
        if self.line_end < self.line_start:
            raise ValueError("line_end must be >= line_start")
        return self


class MarkdownProvenance(ProvenanceBase):
    kind: Literal["markdown"]
    heading: str = Field(min_length=1)


class CodeProvenance(ProvenanceBase):
    kind: Literal["code"]
    symbol: str | None = None
    callsite: str | None = None

    @model_validator(mode="after")
    def _validate_symbol_or_callsite(self) -> "CodeProvenance":
        symbol = (self.symbol or "").strip()
        callsite = (self.callsite or "").strip()
        if not symbol and not callsite:
            raise ValueError("code provenance requires 'symbol' or 'callsite'")
        return self


Provenance = Annotated[MarkdownProvenance | CodeProvenance, Field(discriminator="kind")]


class IRNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    type: str = Field(min_length=1)
    status: IRStatus
    provenance: Provenance


class IREdge(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    from_id: str = Field(alias="from", min_length=1)
    to_id: str = Field(alias="to", min_length=1)
    type: str = Field(min_length=1)
    status: IRStatus
    provenance: Provenance


class IRDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    generated_at: AwareDatetime
    nodes: list[IRNode]
    edges: list[IREdge]


def ir_json_schema() -> dict:
    return IRDocument.model_json_schema()


def make_empty_ir(*, version: str, generated_at: datetime) -> IRDocument:
    return IRDocument(version=version, generated_at=generated_at, nodes=[], edges=[])

