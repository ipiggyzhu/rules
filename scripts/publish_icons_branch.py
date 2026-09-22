"""Publish the `icons/` folder as the root of a standalone `icons` branch.

Why this exists
---------------
jsDelivr rejects any uncached file once a "package" exceeds 50 MB, answering
`403 Package size exceeded the configured limit of 50 MB`. A package is one
repository at one ref. The `main` branch is roughly 86 MB, almost entirely from
the two generated `ad-rules.list` files (~68 MB together), so icons served from
`@main` failed intermittently: whatever happened to be cached was returned, and
everything else was refused.

Serving icons from an orphan branch that contains only this folder keeps that
package around 15 MB, comfortably under the cap, without shrinking the rule
lists or moving the icons out of the repository.

Run this after adding, removing, or renaming any icon:

    python scripts/fix_icon_manifests.py     # rewrite the manifest URLs
    python scripts/publish_icons_branch.py   # republish the icons branch

Then purge the CDN cache for the two manifests so clients pick up the change.
"""

import os
import subprocess
import sys

REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ICONS_BRANCH_NAME = "icons"
ICONS_DIRECTORY_IN_MAIN = "icons"
JSDELIVR_PACKAGE_LIMIT_BYTES = 50 * 1024 * 1024


def run_git(arguments, inputText=None):
    completed = subprocess.run(
        ["git"] + arguments,
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        input=inputText,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "git %s failed: %s" % (" ".join(arguments), completed.stderr.strip())
        )
    return completed.stdout.strip()


def measure_tree_size(treeHash):
    listing = run_git(["ls-tree", "-r", "-l", treeHash])
    totalBytes = 0
    fileCount = 0
    for line in listing.splitlines():
        parts = line.split()
        # Format: <mode> blob <hash> <size>\t<path>
        if len(parts) >= 4 and parts[1] == "blob" and parts[3].isdigit():
            totalBytes += int(parts[3])
            fileCount += 1
    return totalBytes, fileCount


def main():
    uncommittedChanges = run_git(["status", "--porcelain", "--", ICONS_DIRECTORY_IN_MAIN])
    if uncommittedChanges:
        print("Refusing to publish: commit your icons/ changes first.")
        print(uncommittedChanges)
        return 1

    iconsTreeHash = run_git(["rev-parse", "HEAD:%s" % ICONS_DIRECTORY_IN_MAIN])
    totalBytes, fileCount = measure_tree_size(iconsTreeHash)

    print("icons tree      :", iconsTreeHash)
    print("files           :", fileCount)
    print("package size    : %.1f MB (jsDelivr limit %.0f MB)" % (
        totalBytes / (1024 * 1024), JSDELIVR_PACKAGE_LIMIT_BYTES / (1024 * 1024)))

    if totalBytes >= JSDELIVR_PACKAGE_LIMIT_BYTES:
        print()
        print("REFUSING TO PUBLISH: the icons folder alone now exceeds the jsDelivr")
        print("limit, so serving it from a dedicated branch would not help.")
        return 1

    commitMessage = (
        "chore: icons-only branch so jsDelivr sees a package under its 50 MB limit"
    )
    orphanCommitHash = run_git(["commit-tree", iconsTreeHash], inputText=commitMessage)
    run_git(["branch", "-f", ICONS_BRANCH_NAME, orphanCommitHash])

    print("orphan commit   :", orphanCommitHash)
    print("branch updated  :", ICONS_BRANCH_NAME)
    print()
    print("Now push it and purge the CDN cache:")
    print("  git push --force origin %s" % ICONS_BRANCH_NAME)
    print("  curl https://purge.jsdelivr.net/gh/ipiggyzhu/rules@%s/loon.json"
          % ICONS_BRANCH_NAME)
    return 0


if __name__ == "__main__":
    sys.exit(main())
