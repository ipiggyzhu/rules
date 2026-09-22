"""Repair the Loon / Quantumult X icon manifests.

Fixes three problems found in the committed manifests:

1. `quantumultx.json` points at `AllIcon/<name>.png`, a directory that does not
   exist in this repository. The images actually live in `icons/images/`.
2. A few entries use the wrong capitalisation (for example `Youtube.png` when the
   file on disk is `youtube.png`). Raw GitHub and jsDelivr are case-sensitive, so
   those entries return 404.
3. Icons were served from `raw.githubusercontent.com`, which is frequently
   unreachable on mainland China mobile networks, so the manifests now point at
   the jsDelivr CDN instead.

Run: python scripts/fix_icon_manifests.py
"""

import json
import os
import urllib.parse

REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIRECTORY = os.path.join(REPOSITORY_ROOT, "icons", "images")

MANIFEST_RELATIVE_PATHS = ["icons/loon.json", "icons/quantumultx.json"]

# jsDelivr serves the repo contents from a CDN that stays reachable where
# raw.githubusercontent.com often does not.
#
# Use the canonical cdn.jsdelivr.net rather than a provider-specific hostname
# such as testingcf.jsdelivr.net. The testingcf node was observed serving a
# stale copy of this manifest for well over 15 minutes after two successful
# cache purges, while every other node served the current file. The canonical
# hostname load-balances across providers and avoids being pinned to one of
# them.
ICON_URL_PREFIX = "https://cdn.jsdelivr.net/gh/ipiggyzhu/rules@main/icons/images/"


def build_case_insensitive_index(fileNames):
    index = {}
    for fileName in fileNames:
        index.setdefault(fileName.lower(), fileName)
    return index


def rewrite_manifest(manifestRelativePath, imageNameByLowercase, imageNames):
    manifestPath = os.path.join(REPOSITORY_ROOT, manifestRelativePath)
    with open(manifestPath, encoding="utf-8") as handle:
        manifestData = json.load(handle)

    iconEntries = manifestData.get("icons", [])
    repointedCount = 0
    caseFixedCount = 0
    unresolvedEntries = []

    for entry in iconEntries:
        originalUrl = entry.get("url", "")
        if not originalUrl:
            continue

        requestedFileName = urllib.parse.unquote(originalUrl.rsplit("/", 1)[-1])

        resolvedFileName = None
        if requestedFileName in imageNames:
            resolvedFileName = requestedFileName
        elif requestedFileName.lower() in imageNameByLowercase:
            resolvedFileName = imageNameByLowercase[requestedFileName.lower()]
            caseFixedCount += 1
        else:
            unresolvedEntries.append((entry.get("name"), requestedFileName))
            continue

        # quote() leaves the parentheses common in these filenames alone, so pass
        # them explicitly as characters that must be escaped.
        encodedFileName = urllib.parse.quote(resolvedFileName, safe="")
        rebuiltUrl = ICON_URL_PREFIX + encodedFileName
        if rebuiltUrl != originalUrl:
            entry["url"] = rebuiltUrl
            repointedCount += 1

    if unresolvedEntries:
        manifestData["icons"] = [
            entry
            for entry in iconEntries
            if urllib.parse.unquote(entry.get("url", "").rsplit("/", 1)[-1]).lower()
            in imageNameByLowercase
        ]

    with open(manifestPath, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifestData, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(manifestRelativePath)
    print("  entries total          :", len(iconEntries))
    print("  urls repointed         :", repointedCount)
    print("  capitalisation repaired:", caseFixedCount)
    print("  dropped (no such image):", len(unresolvedEntries))
    for iconName, fileName in unresolvedEntries:
        print("       %s -> %s" % (iconName, fileName))
    print("  entries kept           :", len(manifestData["icons"]))


def main():
    imageNames = set(os.listdir(IMAGES_DIRECTORY))
    imageNameByLowercase = build_case_insensitive_index(imageNames)
    print("images available on disk:", len(imageNames))
    print()

    for manifestRelativePath in MANIFEST_RELATIVE_PATHS:
        rewrite_manifest(manifestRelativePath, imageNameByLowercase, imageNames)
        print()


if __name__ == "__main__":
    main()
