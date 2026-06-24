from __future__ import annotations

import json
from pathlib import Path
import re

from skill_research.core.serialization import to_json_safe
from skill_research.core.types import SkillRef
from skill_research.llms.base import ChatMessage, CompletionRequest, CompletionResponse
from skill_research.patches.types import Patch, PatchPool
from skill_research.traces.types import TraceRecord

PATCH_SYSTEM_PROMPT = """You are a strict skill patch generator.
Return only JSON with this exact shape:
{"patches":[{"patch_id":"short-id","patch_type":"guidance","target_file":"SKILL.md","target_section":null,"operation":"append_document","content":"Concrete skill guidance to append. Must be non-empty.","supported_trace_ids":["task-id"],"metadata":{}}]}
Every patch must use exactly these fields and no aliases. Do not output delta_tokens or support_count; the harness computes them. The content field is the actual text appended to SKILL.md.
"""


class PatchSchemaError(ValueError):
    pass


def _count_tokens(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9_']+", text))


def build_patch_messages(skill_path: Path, traces: list[TraceRecord], k: int) -> list[ChatMessage]:
    skill_file = skill_path / "SKILL.md" if skill_path.is_dir() else skill_path
    skill_text = skill_file.read_text(encoding="utf-8") if skill_file.exists() else ""
    trace_lines = []
    for trace in traces:
        if trace.success:
            continue
        payload = json.dumps(to_json_safe(trace.payload), sort_keys=True)
        trace_lines.append(f"task_id={trace.task_id}\nfailure_type={trace.failure_type}\npayload={payload}")
    return [
        ChatMessage("system", PATCH_SYSTEM_PROMPT),
        ChatMessage("user", f"Current skill:\n{skill_text}\nFailed traces:\n{chr(10).join(trace_lines)}\nGenerate up to {k} patches."),
    ]


class OpenAITracePatchProposer:
    name = "openai_trace"

    def __init__(self, backend=None, temperature: float = 0.2, max_tokens: int = 2500):
        self.backend = backend
        self.temperature = temperature
        self.max_tokens = max_tokens

    def parse_response(self, content: str, valid_trace_ids: set[str] | None = None) -> list[Patch]:
        payload = json.loads(content)
        if set(payload) != {"patches"}:
            raise PatchSchemaError("Patch response must contain only a patches field")
        if not isinstance(payload["patches"], list):
            raise PatchSchemaError("patches must be a list")
        required = {"patch_id", "patch_type", "target_file", "target_section", "operation", "content", "supported_trace_ids"}
        optional = {"metadata"}
        allowed = required | optional
        patches = []
        for index, patch in enumerate(payload["patches"]):
            if not isinstance(patch, dict):
                raise PatchSchemaError(f"Patch {index} must be an object")
            unexpected = set(patch) - allowed
            if unexpected:
                raise PatchSchemaError(f"Unexpected patch fields: {sorted(unexpected)}")
            missing = required - set(patch)
            if missing:
                raise PatchSchemaError(f"Missing patch fields: {sorted(missing)}")
            if not patch["content"] and patch["operation"] != "no_op":
                raise PatchSchemaError("content must be non-empty for non-noop patches")
            supported_trace_ids = patch["supported_trace_ids"]
            if not isinstance(supported_trace_ids, list) or not all(isinstance(item, str) for item in supported_trace_ids):
                raise PatchSchemaError("supported_trace_ids must be a list of strings")
            if valid_trace_ids is not None:
                unknown = set(supported_trace_ids) - valid_trace_ids
                if unknown:
                    raise PatchSchemaError(f"Unknown supported_trace_ids: {sorted(unknown)}")
            metadata = dict(patch.get("metadata", {}))
            metadata["supported_trace_ids"] = supported_trace_ids
            patches.append(
                Patch(
                    patch_id=patch["patch_id"],
                    patch_type=patch["patch_type"],
                    target_file=patch["target_file"],
                    target_section=patch["target_section"],
                    operation=patch["operation"],
                    content=patch["content"],
                    delta_tokens=_count_tokens(patch["content"]),
                    support_count=len(set(supported_trace_ids)),
                    metadata=metadata,
                )
            )
        return patches

    def propose(self, skill: SkillRef, traces: list[TraceRecord], config: dict) -> PatchPool:
        if self.backend is None:
            return PatchPool([])
        k = int(config.get("k", config.get("patch_count", 8)))
        messages = build_patch_messages(skill.path, traces, k)
        response = self.backend.complete(CompletionRequest(messages=messages, temperature=self.temperature, max_tokens=self.max_tokens))
        content = response.content if isinstance(response, CompletionResponse) else str(response)
        valid_trace_ids = {trace.task_id for trace in traces}
        patches = self.parse_response(content, valid_trace_ids=valid_trace_ids)
        return PatchPool(patches, metadata={"proposer": self.name, "raw_response": content})
