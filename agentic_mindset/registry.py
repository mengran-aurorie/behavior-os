import os
from pathlib import Path
from typing import Optional
from agentic_mindset.pack import CharacterPack


_DEFAULT_USER_REGISTRY = Path.home() / ".agentic-mindset" / "registry"
_DEFAULT_LOCAL_REGISTRY = Path("characters")


class CharacterRegistry:
    def __init__(self, search_paths: Optional[list[Path]] = None):
        if search_paths is not None:
            self._search_paths = [Path(p) for p in search_paths]
        else:
            self._search_paths = self._resolve_default_paths()

    @staticmethod
    def _resolve_default_paths() -> list[Path]:
        paths = []
        env = os.environ.get("AGENTIC_MINDSET_REGISTRY")
        if env:
            paths.append(Path(env))
        paths.append(_DEFAULT_USER_REGISTRY)
        paths.append(_DEFAULT_LOCAL_REGISTRY)
        return paths

    def load_path(self, path: Path) -> CharacterPack:
        return CharacterPack.load(Path(path))

    def load_id(self, character_id: str) -> CharacterPack:
        for search_path in self._search_paths:
            candidate = search_path / character_id
            if candidate.is_dir():
                return CharacterPack.load(candidate)
        raise KeyError(f"Character not found: {character_id!r} (searched: {self._search_paths})")

    def list_ids(self) -> list[str]:
        seen = set()
        ids = []
        for search_path in self._search_paths:
            if not search_path.is_dir():
                continue
            for entry in sorted(search_path.iterdir()):
                if entry.is_dir() and entry.name not in seen:
                    seen.add(entry.name)
                    ids.append(entry.name)
        return ids
