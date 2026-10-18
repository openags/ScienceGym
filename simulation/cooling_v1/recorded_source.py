"""Locate exact source bytes pinned by a historical execution receipt."""
from pathlib import Path
from trace_store import sha
from world import HERE


def recorded_source(name, expected):
    current=HERE/name
    if current.exists() and sha(current)==expected:
        return current
    archived=HERE/'source_history'/expected/Path(name).name
    if archived.exists() and sha(archived)==expected:
        return archived
    # Return the original path so the caller reports a mismatch or absence.
    return current
