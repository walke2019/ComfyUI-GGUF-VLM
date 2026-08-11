"""File-level batch manifest helpers."""

from pathlib import Path


def build_image_manifest(root, extensions=None):
    extensions = {ext.lower() for ext in (extensions or [".png", ".jpg", ".jpeg", ".webp", ".bmp"])}
    base = Path(root)
    if not base.exists():
        return []
    rows = []
    for path in sorted(base.rglob("*")):
        if path.is_file() and path.suffix.lower() in extensions:
            rows.append({
                "path": str(path.as_posix()),
                "name": path.name,
                "stem": path.stem,
                "extension": path.suffix.lower(),
            })
    return rows

