"""Export tracked source bytes for review, independently of any agent task store.

This is a source snapshot, not proof that tests passed. Environment-file names,
symlinks and untracked files are excluded/rejected; this is not a secret scanner.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import zipfile


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root).decode("utf-8")


def export_workspace(root: Path, output: Path | None = None) -> dict:
    root = root.resolve(strict=True)
    output = (output or root / ".reports").resolve()
    commit = git(root, "rev-parse", "HEAD").strip()
    tree = git(root, "rev-parse", "HEAD^{tree}").strip()
    paths = sorted(filter(None, git(root, "ls-files", "-z").split("\0")))
    status = git(root, "status", "--porcelain=v1", "--untracked-files=no")
    if not paths:
        raise RuntimeError("No tracked source files")

    # Validate and read once. The archive and all hashes use the very same bytes.
    contents: dict[str, bytes] = {}
    for name in paths:
        path = root / name
        if (path.is_symlink() or not path.resolve().is_relative_to(root)
                or not path.is_file()):
            raise RuntimeError("Unexpected tracked source path: " + name)
        if path.resolve().is_relative_to(output):
            raise RuntimeError("Evidence output must not be tracked: " + name)
        if path.name == ".env" or path.name.startswith(".env."):
            raise RuntimeError("Environment files must not be tracked in the export")
        contents[name] = path.read_bytes()

    digest = hashlib.sha256()
    files = {}
    for name, data in contents.items():
        digest.update(name.encode("utf-8") + b"\0" + data + b"\0")
        files[name] = hashlib.sha256(data).hexdigest()
    if git(root, "rev-parse", "HEAD").strip() != commit:
        raise RuntimeError("HEAD moved during source export; retry after reconciliation")
    identity = {
        "schema_version": 2,
        "commit": commit,
        "tree": tree,
        "source_sha256": digest.hexdigest(),
        "working_tree_dirty": bool(status),
        "platform": platform.platform(),
        "run_id": os.getenv("GITHUB_RUN_ID"),
        "files": files,
        "note": (
            "Hashes identify the archived working-tree bytes, not a passing test result. "
            "Commit/tree identify the checkout base; dirty bytes can differ from that base. "
            "Actual outcomes come from CI logs and browser/native reports."
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="source-export-", dir=output) as directory:
        staging = Path(directory)
        archive_path = staging / "workspace.zip"
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in contents.items():
                archive.writestr(name, data)
        # Link the pair, so an interrupted publication can be detected by readers.
        identity["archive_sha256"] = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        identity_path = staging / "workspace.json"
        identity_path.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
        archive_path.replace(output / "workspace.zip")
        identity_path.replace(output / "workspace.json")
    return identity


def main() -> None:
    identity = export_workspace(Path(__file__).resolve().parents[1])
    print(json.dumps({key: value for key, value in identity.items() if key != "files"}))


if __name__ == "__main__":
    main()
