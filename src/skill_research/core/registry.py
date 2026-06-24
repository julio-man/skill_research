"""Small registry helper for constructing named swappable components."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class ComponentRegistry(Generic[T]):
    def __init__(self) -> None:
        self._builders: dict[str, Callable[..., T]] = {}

    def register(self, name: str, builder: Callable[..., T]) -> None:
        if name in self._builders:
            raise ValueError(f"Component '{name}' is already registered")
        self._builders[name] = builder

    def build(self, name: str, **kwargs) -> T:
        if name not in self._builders:
            known = ", ".join(self.names()) or "none"
            raise KeyError(f"Unknown component '{name}'. Known components: {known}")
        return self._builders[name](**kwargs)

    def names(self) -> list[str]:
        return sorted(self._builders)
