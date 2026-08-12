"""ppc-os — Campaign management toolkit for Claude Code."""

__version__ = "0.1.0"

from pathlib import Path


def get_project_root() -> Path:
    """Find the project root directory.

    When running inside a client repo (e.g., brcc-marketing/) that includes
    ppc-os as a submodule, config/ and data/ live in the client repo, not
    inside the submodule. This function checks the CWD first, then falls
    back to the module-relative path for standalone ppc-os usage.

    The project root is whichever directory contains a config/ folder.
    """
    # Check CWD first (handles submodule/client repo layout)
    cwd = Path.cwd()
    if (cwd / "config").is_dir():
        return cwd

    # Fall back to module-relative path (standalone ppc-os usage)
    module_root = Path(__file__).resolve().parent.parent
    if (module_root / "config").is_dir():
        return module_root

    # Last resort: CWD even without config/ (let callers handle missing files)
    return cwd
