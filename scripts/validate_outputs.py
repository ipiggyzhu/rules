"""Validate the Loon config, icon manifests, and generated rule lists.

Run: python scripts/validate_outputs.py

Exits non-zero if anything is inconsistent, so it can be wired into CI later.
"""

import json
import os
import re
import urllib.parse

REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BUILTIN_POLICIES = {"DIRECT", "REJECT", "REJECT-DROP", "REJECT-TINYGIF", "PROXY"}

KNOWN_RULE_TYPES = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "IP-CIDR",
    "IP-CIDR6",
    "GEOIP",
    "IP-ASN",
    "DEST-PORT",
    "SRC-PORT",
    "PROTOCOL",
    "FINAL",
    "AND",
    "OR",
    "NOT",
}

# Leaving any of these unset (or setting dns-server) would reopen a DNS leak.
REQUIRED_GENERAL_SETTINGS = {
    "ip-mode": "ipv4-only",
    "hijack-dns": "*:53",
    "udp-fallback-mode": "REJECT",
    "disable-stun": "true",
    "ipv6-vif": "off",
}

EXPECTED_ICON_HOST = "cdn.jsdelivr.net"

RULE_LIST_PATHS = [
    "Loon/ad-rules.list",
    "Loon/direct-rules.list",
    "QuantumultX/ad-rules.list",
    "QuantumultX/direct-rules.list",
]


def parse_config_sections(configPath):
    sections = {}
    currentSection = None
    for lineNumber, rawLine in enumerate(
        open(configPath, encoding="utf-8").read().splitlines(), 1
    ):
        stripped = rawLine.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            currentSection = stripped[1:-1]
            sections.setdefault(currentSection, [])
            continue
        if not stripped or stripped.startswith("#") or currentSection is None:
            continue
        sections[currentSection].append((lineNumber, stripped))
    return sections


def validate_loon_config(problems):
    configPath = os.path.join(REPOSITORY_ROOT, "Loon/loon.lcf")
    sections = parse_config_sections(configPath)

    definedPolicies = set()
    for _, line in sections.get("Proxy Group", []):
        definedPolicies.add(line.split("=", 1)[0].strip())
    for _, line in sections.get("Remote Filter", []):
        definedPolicies.add(line.split("=", 1)[0].strip())

    allowedTargets = definedPolicies | BUILTIN_POLICIES

    for lineNumber, line in sections.get("Rule", []):
        parts = [segment.strip() for segment in line.split(",")]
        ruleType = parts[0].upper()
        if ruleType not in KNOWN_RULE_TYPES:
            problems.append(f"loon.lcf L{lineNumber}: unknown rule type {ruleType}")
            continue
        if ruleType == "FINAL":
            target = parts[1]
        elif parts[-1] == "no-resolve":
            target = parts[-2]
        else:
            target = parts[-1]
        if target not in allowedTargets:
            problems.append(f"loon.lcf L{lineNumber}: undefined policy {target}")

    for sectionName in ("Remote Rule", "Plugin"):
        for lineNumber, line in sections.get(sectionName, []):
            match = re.search(r"policy=([^,]+)", line)
            if match and match.group(1).strip() not in allowedTargets:
                problems.append(
                    f"loon.lcf L{lineNumber}: undefined policy {match.group(1).strip()}"
                )

    generalSettings = {}
    for _, line in sections.get("General", []):
        if "=" in line:
            key, value = line.split("=", 1)
            generalSettings[key.strip()] = value.strip()

    for key, expectedValue in REQUIRED_GENERAL_SETTINGS.items():
        actualValue = generalSettings.get(key)
        if actualValue != expectedValue:
            problems.append(
                f"loon.lcf [General]: {key} is {actualValue!r}, expected {expectedValue!r}"
            )

    if "dns-server" in generalSettings:
        problems.append(
            "loon.lcf [General]: dns-server is set; plaintext DNS would leak"
        )

    dohServers = generalSettings.get("doh-server", "")
    if not dohServers:
        problems.append("loon.lcf [General]: doh-server missing")
    else:
        for endpoint in dohServers.split(","):
            hostName = urllib.parse.urlparse(endpoint.strip()).hostname or ""
            # An IP literal needs no bootstrap DNS lookup; a hostname does.
            if not re.fullmatch(r"[0-9.]+", hostName):
                problems.append(
                    f"loon.lcf [General]: doh-server {hostName} is a hostname, "
                    "which needs a plaintext bootstrap lookup"
                )

    print("loon.lcf     : %d sections, %d rules, %d policies" % (
        len(sections), len(sections.get("Rule", [])), len(definedPolicies)))
    print("               ip-mode=%s  doh-server=%d endpoint(s)  dns-server=%s" % (
        generalSettings.get("ip-mode"),
        len(dohServers.split(",")) if dohServers else 0,
        "absent" if "dns-server" not in generalSettings else "PRESENT",
    ))


def validate_icon_manifests(problems):
    imagesOnDisk = set(os.listdir(os.path.join(REPOSITORY_ROOT, "icons", "images")))

    for manifestRelativePath in ("icons/loon.json", "icons/quantumultx.json"):
        manifestPath = os.path.join(REPOSITORY_ROOT, manifestRelativePath)
        manifestData = json.load(open(manifestPath, encoding="utf-8"))
        entries = manifestData.get("icons", [])

        wrongHostCount = 0
        missingFileCount = 0
        for entry in entries:
            url = entry.get("url", "")
            if EXPECTED_ICON_HOST not in url:
                wrongHostCount += 1
            fileName = urllib.parse.unquote(url.rsplit("/", 1)[-1])
            if fileName not in imagesOnDisk:
                missingFileCount += 1
                problems.append(
                    f"{manifestRelativePath}: {entry.get('name')} -> {fileName} not on disk"
                )

        if wrongHostCount:
            problems.append(
                f"{manifestRelativePath}: {wrongHostCount} urls not on {EXPECTED_ICON_HOST}"
            )

        print("%-22s: %d entries, %d wrong host, %d missing file" % (
            manifestRelativePath, len(entries), wrongHostCount, missingFileCount))


def validate_rule_lists(problems):
    for relativePath in RULE_LIST_PATHS:
        fullPath = os.path.join(REPOSITORY_ROOT, relativePath)

        declaredTotal = None
        ruleLines = []
        for line in open(fullPath, encoding="utf-8"):
            stripped = line.strip()
            if stripped.startswith("# Total:"):
                declaredTotal = int(stripped.split(":", 1)[1].strip())
            if stripped and not stripped.startswith("#"):
                ruleLines.append(stripped)

        if declaredTotal != len(ruleLines):
            problems.append(
                f"{relativePath}: header says {declaredTotal} but file has {len(ruleLines)}"
            )

        ipRulesMissingNoResolve = [
            rule
            for rule in ruleLines
            if rule.startswith(("IP-CIDR,", "IP-CIDR6,")) and not rule.endswith(",no-resolve")
        ]
        if ipRulesMissingNoResolve:
            problems.append(
                f"{relativePath}: {len(ipRulesMissingNoResolve)} ip rules lack no-resolve"
            )

        sizeInMegabytes = os.path.getsize(fullPath) / (1024 * 1024)
        print("%-30s: %8d rules  %5.1f MB  ip-no-resolve ok=%s" % (
            relativePath, len(ruleLines), sizeInMegabytes,
            not ipRulesMissingNoResolve))


def validate_no_secrets(problems):
    secretPattern = re.compile(r"token=[0-9a-f]{16,}", re.IGNORECASE)
    for directoryPath, directoryNames, fileNames in os.walk(REPOSITORY_ROOT):
        if ".git" in directoryPath or "icons" in directoryPath:
            continue
        for fileName in fileNames:
            if not fileName.endswith((".js", ".py", ".conf", ".lcf", ".json", ".yml")):
                continue
            filePath = os.path.join(directoryPath, fileName)
            try:
                content = open(filePath, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            if secretPattern.search(content):
                problems.append(
                    f"{os.path.relpath(filePath, REPOSITORY_ROOT)}: contains a subscription token"
                )
    print("secret scan  : done")


def main():
    problems = []
    validate_loon_config(problems)
    print()
    validate_icon_manifests(problems)
    print()
    validate_rule_lists(problems)
    print()
    validate_no_secrets(problems)

    print()
    if problems:
        print("PROBLEMS (%d):" % len(problems))
        for problem in problems[:20]:
            print("  -", problem)
        raise SystemExit(1)

    print("ALL VALIDATIONS PASSED")


if __name__ == "__main__":
    main()
