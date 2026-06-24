from skill_research.core.registry import ComponentRegistry
from skill_research.patches.appliers.skill_directory import SkillDirectoryPatchApplier


applier_registry = ComponentRegistry()
applier_registry.register("skill_directory", lambda **kwargs: SkillDirectoryPatchApplier())


def build_applier(name: str, **kwargs):
    return applier_registry.build(name, **kwargs)


__all__ = ["SkillDirectoryPatchApplier", "applier_registry", "build_applier"]
