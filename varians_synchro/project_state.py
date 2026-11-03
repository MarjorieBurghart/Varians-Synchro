"""Reliable, UI-independent detection of project changes since the last save.

The project is a JSON-serializable dictionary and nested editors mutate it in
place. Comparing its persisted JSON representation catches every such mutation,
without a fragile collection of per-button `dirty = True` assignments.
"""
from __future__ import annotations

import hashlib
import json


def project_fingerprint(project: dict) -> str:
    """A deterministic fingerprint of the whole JSON-persisted project."""
    content = json.dumps(project, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class ProjectChangeTracker:
    def __init__(self, project: dict, *, newly_created: bool = False):
        self._saved_fingerprint = project_fingerprint(project)
        self._newly_created = bool(newly_created)

    def is_modified(self, project: dict) -> bool:
        return self._newly_created or project_fingerprint(project) != self._saved_fingerprint

    def mark_saved(self, project: dict) -> None:
        """Call only after an actual, successful on-disk save."""
        self._saved_fingerprint = project_fingerprint(project)
        self._newly_created = False

    def reset(self, project: dict, *, newly_created: bool = False) -> None:
        """New document or successfully opened document, not a mere UI refresh."""
        self._saved_fingerprint = project_fingerprint(project)
        self._newly_created = bool(newly_created)
