#!/usr/bin/env python3
"""Install the bundled SynQuest Codex skill into CODEX_HOME."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "skills" / "synquest"
    if not source.exists():
        raise SystemExit(f"Skill source not found: {source}")

    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    target = codex_home / "skills" / "SynQuest"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, dirs_exist_ok=True)
    print(f"Installed SynQuest skill to {target}")


if __name__ == "__main__":
    main()
