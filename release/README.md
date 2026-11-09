# Build the public download

From the project root run `python3 release/build_free.py ../autosave.zip`. Only files enumerated in `release/free-files.txt` enter the ZIP. Review changes to that list before packaging. Keep buyer-only source outside this repository. The builder rejects missing files, duplicate entries, absolute paths, parent traversal, and symlinks.
