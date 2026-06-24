from __future__ import annotations

import pytest

from skill_research.patches.proposers.openai_trace import PatchSchemaError, OpenAITracePatchProposer


def test_openai_trace_parser_rejects_id_alias() -> None:
    with pytest.raises(PatchSchemaError, match="Unexpected patch fields"):
        OpenAITracePatchProposer().parse_response('{"patches": [{"id": "p1", "operation": "append_document", "content": "Rule", "supported_trace_ids": ["t1"]}]}')


def test_openai_trace_parser_rejects_content_aliases() -> None:
    with pytest.raises(PatchSchemaError, match="Unexpected patch fields"):
        OpenAITracePatchProposer().parse_response('{"patches": [{"patch_id": "p1", "patch_type": "guidance", "target_file": "SKILL.md", "target_section": null, "operation": "append_document", "guidance": "Rule"}]}')


def test_openai_trace_parser_rejects_extra_fields() -> None:
    with pytest.raises(PatchSchemaError, match="Unexpected"):
        OpenAITracePatchProposer().parse_response('{"patches": [{"patch_id": "p1", "patch_type": "guidance", "target_file": "SKILL.md", "target_section": null, "operation": "append_document", "content": "Rule", "title": "extra"}]}')
