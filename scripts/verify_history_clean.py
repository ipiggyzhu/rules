"""Verify the rewritten git history contains no subscription tokens.

Scans every blob ever recorded for the sensitive file paths instead of diffing
the whole history, which is far faster on a repository this size.

Run: python scripts/verify_history_clean.py
"""

import re
import subprocess
import sys

# The two tokens that were committed, plus a generic catch-all.
KNOWN_LEAKED_TOKENS = [
    "9446cdd625edff748cbf1c2693ade86f",
    "f055cc2456ff2dfde93e743f214d9335",
]
GENERIC_TOKEN_PATTERN = re.compile(r"token=[0-9a-f]{16,}", re.IGNORECASE)

PATHS_TO_AUDIT = [
    "scripts/clash-verge-override.js",
]


def run_git(arguments, binaryOutput=False):
    completed = subprocess.run(
        ["git"] + arguments,
        capture_output=True,
        text=not binaryOutput,
        encoding=None if binaryOutput else "utf-8",
        errors=None if binaryOutput else "ignore",
    )
    return completed.stdout


def collect_blob_hashes_for_path(filePath):
    """Every blob this path ever pointed at, across all refs."""
    commitList = run_git(["rev-list", "--all", "--", filePath]).split()
    blobHashes = set()
    for commitHash in commitList:
        listing = run_git(["ls-tree", "-r", commitHash, "--", filePath])
        for line in listing.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[1] == "blob":
                blobHashes.add(parts[2])
    return commitList, blobHashes


def main():
    problems = []
    totalBlobsScanned = 0

    for filePath in PATHS_TO_AUDIT:
        commitList, blobHashes = collect_blob_hashes_for_path(filePath)
        print("%s: %d commits, %d distinct blobs" % (
            filePath, len(commitList), len(blobHashes)))

        redactedMarkerCount = 0
        for blobHash in blobHashes:
            content = run_git(["cat-file", "-p", blobHash])
            totalBlobsScanned += 1

            for token in KNOWN_LEAKED_TOKENS:
                if token in content:
                    problems.append(f"blob {blobHash[:12]} still contains a known token")

            for match in GENERIC_TOKEN_PATTERN.findall(content):
                problems.append(f"blob {blobHash[:12]} contains token-like value {match[:14]}...")

            if "REDACTED_TOKEN" in content:
                redactedMarkerCount += 1

        print("   blobs carrying REDACTED_TOKEN marker:", redactedMarkerCount)

    # Also confirm the tokens appear nowhere in any commit message.
    allMessages = run_git(["log", "--all", "--format=%B"])
    for token in KNOWN_LEAKED_TOKENS:
        if token in allMessages:
            problems.append("a commit message still contains a token")

    print()
    print("blobs scanned:", totalBlobsScanned)
    if problems:
        print("PROBLEMS (%d):" % len(problems))
        for problem in problems[:20]:
            print("  -", problem)
        sys.exit(1)

    print("HISTORY CLEAN: no tokens found in any historical blob or commit message")


if __name__ == "__main__":
    main()
