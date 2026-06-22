from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from skill_research.llm.client import ChatMessage, LLMClient
from skill_research.patches.types import Patch
from skill_research.traces import TraceRecord


PATCH_SYSTEM_PROMPT = """You are a skill patch generator.
You are given:
1. The current shared skill file content.
2. A small set of execution traces and failure types.
Your job is to propose candidate patches that improve the shared skill.

Return ONLY valid JSON with this schema:
{
  \"patches\": [
    {
      \"patch_id\": \"string\",
      \"patch_type\": \"add_rule|rewrite_section|add_example|add_checklist|add_script|edit_script\",
      \"target_file\": \"SKILL.md|references/<name>.md|scripts/<name>.py\",
      \"target_section\": \"string or null\",
      \"operation\": \"append_under_section|replace_section|append_document|prepend_document\",
      \"content\": \"string\",
      \"delta_tokens\": 0,
      \"support_count\": 1
    }
  ]
}
Do not include commentary outside the JSON.
Prefer concise, targeted patches over large rewrites.
"""



def build_patch_messages(skill_path: Path, traces: list[TraceRecord], k: int) -> list[ChatMessage]:
    resolved_skill_path = skill_path / "SKILL.md" if skill_path.is_dir() else skill_path
    skill_text = resolved_skill_path.read_text(encoding="utf-8")
    summary = OpenAIPatchProposer(model="").build_trace_summary(traces)
    user_prompt = f"""Current skill file (`SKILL.md`):

```markdown
{skill_text}
```

Failed traces summary:
{summary}

Generate up to {k} candidate patches.
Each patch should target the current failure patterns.
"""
    return [
        ChatMessage(role="system", content=PATCH_SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_prompt),
    ]


@dataclass
class OpenAIPatchProposer:
    model: str
    temperature: float = 0.2
    max_tokens: int = 2500

    def build_trace_summary(self, traces: list[TraceRecord], max_traces: int = 5) -> str:
        chosen = traces[:max_traces]
        if not chosen:
            return "No traces available."

        chunks: list[str] = []
        for index, trace in enumerate(chosen, start=1):
            evaluation = trace.evaluation
            metadata = evaluation.get("metadata", {})
            chunks.append(
                f"Trace {index}:\n"
                f"- task_id: {trace.task_id}\n"
                f"- task_instruction: {trace.task_instruction}\n"
                f"- failure_type: {evaluation.get('failure_type')}\n"
                f"- execution_returncode: {trace.execution_returncode}\n"
                f"- execution_stderr: {trace.execution_stderr[:1000]}\n"
                f"- raw_model_output: {trace.raw_model_output[:1500]}\n"
                f"- expected_region_values: {json.dumps(metadata.get('expected_region_values', {}), ensure_ascii=False)}\n"
                f"- actual_region_values: {json.dumps(metadata.get('actual_region_values', {}), ensure_ascii=False)}\n"
            )
        return "\n".join(chunks)

    def parse_patch_response(self, content: str) -> list[Patch]:
        payload = json.loads(content)
        patch_dicts = payload.get("patches", [])
        patches: list[Patch] = []
        for index, patch in enumerate(patch_dicts):
            patches.append(
                Patch(
                    patch_id=patch.get("patch_id", f"p{index + 1}"),
                    patch_type=patch["patch_type"],
                    target_file=patch["target_file"],
                    target_section=patch.get("target_section"),
                    operation=patch["operation"],
                    content=patch["content"],
                    delta_tokens=int(patch.get("delta_tokens", 0)),
                    support_count=int(patch.get("support_count", 1)),
                )
            )
        return patches

    def generate(self, skill_path: Path, traces: list[TraceRecord], k: int, llm_client: LLMClient) -> list[Patch]:
        messages = build_patch_messages(skill_path=skill_path, traces=traces, k=k)
        content = llm_client.complete(messages, temperature=self.temperature, max_tokens=self.max_tokens)
        return self.parse_patch_response(content)
