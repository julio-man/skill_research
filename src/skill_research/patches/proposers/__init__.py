from skill_research.core.registry import ComponentRegistry
from skill_research.patches.proposers.openai_trace import OpenAITracePatchProposer
from skill_research.patches.proposers.replay import ReplayPatchProposer


proposer_registry = ComponentRegistry()
proposer_registry.register("openai_trace", lambda **kwargs: OpenAITracePatchProposer(**kwargs))
proposer_registry.register("replay", lambda patch_pool_path, **kwargs: ReplayPatchProposer(patch_pool_path))


def build_proposer(name: str, **kwargs):
    return proposer_registry.build(name, **kwargs)


__all__ = ["OpenAITracePatchProposer", "ReplayPatchProposer", "build_proposer", "proposer_registry"]
