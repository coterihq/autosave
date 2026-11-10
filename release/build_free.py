"""Usage: python3 release/build_free.py OUTPUT.zip"""
import argparse
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description="Package the reviewed free-file manifest.")
parser.add_argument("output", type=Path)
args = parser.parse_args()
names = (root / "release/free-files.txt").read_text().splitlines()
if not names or len(names) != len(set(names)):
    parser.error("empty or duplicate manifest entries")
with NamedTemporaryFile(dir=args.output.parent, delete=False) as temporary:
    staged = Path(temporary.name)
try:
    with ZipFile(staged, "w", compression=ZIP_DEFLATED) as archive:
        for name in names:
            relative = Path(name)
            source = root / relative
            if (not name or relative.is_absolute() or ".." in relative.parts
                    or source.resolve() != source or not source.is_file()):
                parser.error(f"invalid manifest entry {name!r}")
            archive.write(source, f"autosave/{name}")
    os.replace(staged, args.output)
finally:
    staged.unlink(missing_ok=True)
