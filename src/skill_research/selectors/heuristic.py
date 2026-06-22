from __future__ import annotations


class NoOpSelector:
    def select(self, state: dict, patches: list):
        for patch in patches:
            if getattr(patch, 'operation', None) == 'no_op' or getattr(patch, 'patch_id', None) == 'noop':
                return patch
        raise ValueError('No noop patch available')


class SupportCountSelector:
    def select(self, state: dict, patches: list):
        return max(patches, key=lambda patch: (patch.support_count, -patch.delta_tokens, patch.patch_id))


class SmallestPatchSelector:
    def select(self, state: dict, patches: list):
        return min(patches, key=lambda patch: (patch.delta_tokens, -patch.support_count, patch.patch_id))
