"""Correctness and impact tests for converter.remove_redundant_rules.

Run directly: python scripts/_test_dedup.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter import remove_redundant_rules, format_for_loon

REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def assert_equal(actual, expected, label):
    if actual != expected:
        print("  FAIL %s\n    expected: %s\n    actual:   %s" % (label, expected, actual))
        return False
    print("  ok   %s" % label)
    return True


def run_correctness_tests():
    print("correctness tests")
    allPassed = True

    allPassed &= assert_equal(
        remove_redundant_rules(["DOMAIN-SUFFIX,example.com", "DOMAIN-SUFFIX,ad.example.com"]),
        ["DOMAIN-SUFFIX,example.com"],
        "child suffix removed by parent suffix",
    )

    allPassed &= assert_equal(
        remove_redundant_rules(["DOMAIN-SUFFIX,example.com", "DOMAIN,a.example.com"]),
        ["DOMAIN-SUFFIX,example.com"],
        "exact domain removed by covering suffix",
    )

    allPassed &= assert_equal(
        remove_redundant_rules(["DOMAIN-SUFFIX,example.com", "DOMAIN,example.com"]),
        ["DOMAIN-SUFFIX,example.com"],
        "exact domain equal to suffix is removed",
    )

    allPassed &= assert_equal(
        remove_redundant_rules(["DOMAIN-KEYWORD,ads", "DOMAIN-SUFFIX,ads.example.com"]),
        ["DOMAIN-KEYWORD,ads"],
        "domain removed by covering keyword",
    )

    allPassed &= assert_equal(
        remove_redundant_rules(["DOMAIN-KEYWORD,ads", "DOMAIN-KEYWORD,adserver"]),
        ["DOMAIN-KEYWORD,ads"],
        "longer keyword removed by shorter keyword",
    )

    # Must NOT over-remove: sibling domains are independent.
    allPassed &= assert_equal(
        sorted(remove_redundant_rules(["DOMAIN-SUFFIX,a.example.com", "DOMAIN-SUFFIX,b.example.com"])),
        ["DOMAIN-SUFFIX,a.example.com", "DOMAIN-SUFFIX,b.example.com"],
        "sibling suffixes both kept",
    )

    # Must NOT treat a partial label as a parent: "ample.com" is not a parent of "example.com".
    allPassed &= assert_equal(
        sorted(remove_redundant_rules(["DOMAIN-SUFFIX,ample.com", "DOMAIN-SUFFIX,example.com"])),
        ["DOMAIN-SUFFIX,ample.com", "DOMAIN-SUFFIX,example.com"],
        "partial label is not a parent suffix",
    )

    # Non-domain rule types must pass through untouched.
    allPassed &= assert_equal(
        remove_redundant_rules(["IP-CIDR,1.2.3.0/24,no-resolve", "USER-AGENT,Foo*"]),
        ["IP-CIDR,1.2.3.0/24,no-resolve", "USER-AGENT,Foo*"],
        "ip and user-agent rules untouched",
    )

    # IP rules keep their no-resolve flag through format_for_loon.
    formattedIpRules = format_for_loon(["IP-CIDR,8.8.8.0/24"])
    allPassed &= assert_equal(
        formattedIpRules,
        ["IP-CIDR,8.8.8.0/24,no-resolve"],
        "format_for_loon preserves no-resolve",
    )

    return bool(allPassed)


def measure_impact_on_existing_lists():
    print()
    print("impact on current generated lists")
    for relativePath in [
        "Loon/ad-rules.list",
        "Loon/direct-rules.list",
        "QuantumultX/ad-rules.list",
        "QuantumultX/direct-rules.list",
    ]:
        fullPath = os.path.join(REPOSITORY_ROOT, relativePath)
        if not os.path.exists(fullPath):
            continue

        existingRules = []
        with open(fullPath, encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    existingRules.append(stripped)

        reducedRules = remove_redundant_rules(existingRules)
        removed = len(existingRules) - len(reducedRules)
        percentage = (removed / len(existingRules) * 100) if existingRules else 0
        print("  %-32s %8d -> %8d  (-%d, -%.1f%%)" % (
            relativePath, len(existingRules), len(reducedRules), removed, percentage))


if __name__ == "__main__":
    correctnessPassed = run_correctness_tests()
    measure_impact_on_existing_lists()
    print()
    print("RESULT:", "all correctness tests passed" if correctnessPassed else "FAILURES PRESENT")
    sys.exit(0 if correctnessPassed else 1)
