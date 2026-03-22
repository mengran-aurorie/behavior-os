from __future__ import annotations
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentic_mindset.registry import CharacterRegistry

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


class FusionEngine:
    def __init__(self, registry: "CharacterRegistry"):
        self._registry = registry

    def fuse(
        self,
        characters: list[tuple[str, float]],
        strategy: FusionStrategy = FusionStrategy.blend,
    ) -> ContextBlock:
        return self.fuse_config(FusionConfig(characters=characters, fusion_strategy=strategy))

    def fuse_config(self, config: FusionConfig) -> ContextBlock:
        raw_pairs = config.characters
        total = sum(w for _, w in raw_pairs)
        if total == 0:
            raise ValueError("Weights sum to zero — cannot normalize.")

        if config.fusion_strategy == FusionStrategy.sequential:
            # Warn if weights are non-equal (they are ignored in sequential mode)
            weights = [w for _, w in raw_pairs]
            if len(set(weights)) > 1:
                print(
                    "Warning: sequential strategy ignores weights. "
                    "Character list order determines precedence.",
                    file=sys.stderr,
                )
            # Sequential: preserve list order, equal display weights, no % in preamble
            weighted_packs = [
                (self._registry.load_id(cid), 1.0 / len(raw_pairs))
                for cid, _ in raw_pairs
            ]
            return ContextBlock.from_packs(weighted_packs, show_weights=False)

        # blend / dominant: normalize and sort by weight descending
        weighted_packs = [
            (self._registry.load_id(cid), w / total)
            for cid, w in raw_pairs
        ]
        weighted_packs.sort(key=lambda x: x[1], reverse=True)
        return ContextBlock.from_packs(weighted_packs, show_weights=True)
