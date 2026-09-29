"""Verify and expand the pinned source SDK, without a neighboring product checkout."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import tempfile
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bootstrap(root):
    lock = json.loads((root / "sdk.lock.json").read_text(encoding="utf-8"))
    if lock["schema"] != "glyphshift.sdk-lock/1":
        raise ValueError("unsupported SDK lock")
    source = (root / lock["archive"]).resolve()
    if not source.is_relative_to(root.resolve()) or not source.is_file():
        raise ValueError("SDK archive must be a repository-owned file")
    data = source.read_bytes()
    if len(data) > 16 * 1024 * 1024 or digest(data) != lock["sha256"]:
        raise ValueError("SDK archive digest mismatch")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        if len(entries) > 512 or sum(e.file_size for e in entries) > 32 * 1024 * 1024:
            raise ValueError("SDK archive exceeds limits")
        files = {}
        for entry in entries:
            path = PurePosixPath(entry.filename)
            if (not entry.filename or path.is_absolute() or any(p in (".", "..") for p in entry.filename.split("/"))
                or "\\" in entry.filename or ":" in entry.filename or entry.is_dir()
                or stat.S_ISLNK(entry.external_attr >> 16) or entry.filename.casefold() in files):
                raise ValueError("unsafe or duplicate SDK entry")
            files[entry.filename.casefold()] = (entry.filename, archive.read(entry))
    inventory = {name: content for name,content in files.values()}
    release = json.loads(inventory["sdk-release.json"])
    if release["schema"] != "glyphshift.adapter-sdk/1" or release["version"] != lock["version"] or release["source_commit"] != lock["source_commit"]:
        raise ValueError("SDK provenance mismatch")
    hashes = {name:digest(content) for name,content in inventory.items() if name != "sdk-release.json"}
    if hashes != release["files"]:
        raise ValueError("SDK inventory mismatch")
    installed = root / ".sdk"
    if installed.exists():
        actual = {}
        for path in installed.rglob("*"):
            if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
                raise ValueError("SDK cache contains links")
            if path.is_file():
                actual[path.relative_to(installed).as_posix()] = digest(path.read_bytes())
        if actual != {name:digest(content) for name,content in inventory.items()}:
            raise ValueError("SDK cache changed; remove only the generated .sdk directory and bootstrap again")
    else:
        with tempfile.TemporaryDirectory(prefix=".sdk-staging-", dir=root) as temp:
            for name,content in inventory.items():
                path = Path(temp) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            Path(temp).rename(installed)
    print(f"SDK {lock['version']} verified ({len(inventory)} files)")


if __name__ == "__main__":
    bootstrap(Path(__file__).resolve().parents[1])
