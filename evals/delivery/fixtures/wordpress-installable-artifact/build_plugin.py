from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
PLUGIN = ROOT / "sample-plugin"
DIST = ROOT / "dist"
ZIP_PATH = DIST / "sample-plugin.zip"


def build() -> Path:
    DIST.mkdir(exist_ok=True)
    with ZipFile(ZIP_PATH, "w", ZIP_DEFLATED) as archive:
        for path in sorted(p for p in PLUGIN.rglob("*") if p.is_file()):
            archive.write(
                path,
                Path("sample-plugin") / path.relative_to(PLUGIN),
            )
    return ZIP_PATH


if __name__ == "__main__":
    print(build())
