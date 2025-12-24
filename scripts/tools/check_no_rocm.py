#!/usr/bin/env python3
"""Check repository for disallowed ROCm references or files.

Exit 1 if any of the following are found:
- Paths that include `rocm` or `ROCm` (case-insensitive), e.g., `tests/rocm_max395`
- Any file content containing the token `rocm` (as a whole word, case-insensitive)

This script is intended to run in CI to prevent accidental reintroduction of ROCm-specific
tests, docs, or installation guides. If ROCm support is reintroduced it must go through
maintainer discussion and explicit approval.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.dirname(__file__) + '/../../')
OFFENDING = []
PATH_PATTERN = re.compile(r'\brocm\b', re.IGNORECASE)
CONTENT_PATTERN = re.compile(r'\brocm\b', re.IGNORECASE)

# Files/dirs to explicitly ignore when scanning for content (common large/binary folders)
SKIP_DIRS = {'.git', '.venv', 'venv', 'env', 'build', 'dist', '__pycache__', '.github'}
SKIP_FILES = {'CHANGELOG.md', 'LICENSE'}

for root, dirs, files in os.walk(ROOT):
    # Normalize and skip certain dirs
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

    # Check path components for "rocm"
    rel_root = os.path.relpath(root, ROOT)
    if PATH_PATTERN.search(rel_root.replace('\\', '/')):
        OFFENDING.append(('path', rel_root))

    for fname in files:
        if fname in SKIP_FILES:
            continue
        fpath = os.path.join(root, fname)
        # Check filename for pattern
        rel_path = os.path.relpath(fpath, ROOT)
        if PATH_PATTERN.search(rel_path.replace('\\', '/')):
            OFFENDING.append(('path', rel_path))
            continue
        # Check file content for token
        try:
            with open(fpath, 'r', encoding='utf-8') as fh:
                try:
                    data = fh.read()
                except Exception:
                    # Binary or unreadable; skip content check
                    continue
                if CONTENT_PATTERN.search(data):
                    # Record a short snippet
                    m = CONTENT_PATTERN.search(data)
                    start = max(0, m.start() - 40)
                    end = min(len(data), m.end() + 40)
                    snippet = data[start:end].replace('\n', ' ')
                    OFFENDING.append(('content', rel_path, snippet))
        except (UnicodeDecodeError, PermissionError, IsADirectoryError):
            continue

if OFFENDING:
    print('\nERROR: Disallowed ROCm references detected in repository:')
    for entry in OFFENDING:
        if entry[0] == 'path':
            print(f" - Path match: {entry[1]}")
        else:
            print(f" - Content match in {entry[1]}: ...{entry[2]}...")
    print('\nPolicy: Direct additions of ROCm-specific tests, specs or install guides are blocked by CI.\nIf you need to reintroduce ROCm support, open an Issue and get maintainer approval before a PR.')
    sys.exit(1)

print('OK: No ROCm references found (path or content).')
sys.exit(0)
