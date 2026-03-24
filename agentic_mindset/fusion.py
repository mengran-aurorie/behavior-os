from __future__ import annotations
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentic_mindset.registry import CharacterRegistry
    from agentic_mindset.pack import CharacterPack

from agentic_mindset.context import ContextBlock


class FusionStrategy(str, Enum):
    blend = "blend"
    dominant = "dominant"
    sequential = "sequential"


@dataclass
class FusionConfig:
    characters: list[tuple[str, float]]   # [(id, weight), ...]
    fusion_strategy: FusionStrategy = FusionStrategy.blend
    output_format: str = "plain_text"


@dataclass
class FusionReport:
    """Metadata produced by FusionEngine.fuse() when passed by the caller."""
    personas: list[tuple[str, float]] = field(default_factory=list)
    strategy: str = ""
    removed_items: list[str] = field(default_factory=list)
    dominant_character: str | None = None


class FusionEngine:
    def __init__(self, registry: "CharacterRegistry"):
        self._registry = registry

    def prepare_packs(
        self,
        characters: list[tuple[str, float]],
        strategy: FusionStrategy = FusionStrategy.blend,
    ) -> list[tuple["CharacterPack", float]]:
        """Return normalized, sorted (pack, weight) pairs without building a ContextBlock.

        Loads each character from the registry (performs I/O per pack).
        For blend/dominant: normalize weights and sort by descending weight.
        For sequential: preserve list order, set equal weights (1/N each).
        Caller precondition: characters is non-empty and weights sum to > 0.
        """
        total = sum(w for _, w in characters)
        if total == 0:
            raise ValueError("Weights sum to zero — cannot normalize.")
        if strategy == FusionStrategy.sequential:
            return [
                (self._registry.load_id(cid), 1.0 / len(characters))
                for cid, _ in characters
            ]
        pairs = [(self._registry.load_id(cid), w / total) for cid, w in characters]
        pairs.sort(key=lambda x: x[1], reverse=True)
        return pairs

    def fuse(
        self,
        characters: list[tuple[str, float]],
        strategy: FusionStrategy = FusionStrategy.blend,
        report: "FusionReport | None" = None,
    ) -> ContextBlock:
        return self.fuse_config(
            FusionConfig(characters=characters, fusion_strategy=strategy),
            report=report,
        )

    def fuse_config(self, config: FusionConfig, report: "FusionReport | None" = None) -> ContextBlock:
        raw_pairs = config.characters
        total = sum(w for _, w in raw_pairs)
        if total == 0:
            raise ValueError("Weights sum to zero — cannot normalize.")

        if config.fusion_strategy == FusionStrategy.sequential:
            if len({w for _, w in raw_pairs}) > 1:
                print(
                    "Warning: sequential strategy ignores weights. "
                    "Character list order determines precedence.",
                    file=sys.stderr,
                )

        weighted_packs = self.prepare_packs(raw_pairs, config.fusion_strategy)
        show_weights = config.fusion_strategy != FusionStrategy.sequential

        if report is not None:
            report.personas = [(pack.meta.id, w) for pack, w in weighted_packs]
            report.strategy = config.fusion_strategy.value
            weights = [w for _, w in weighted_packs]
            report.dominant_character = (
                weighted_packs[0][0].meta.id
                if len(set(weights)) > 1
                else None
            )
            report.removed_items = []  # reset; from_packs() will append

        return ContextBlock.from_packs(weighted_packs, show_weights=show_weights, report=report)
