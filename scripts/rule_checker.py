"""检查本地广告黑名单。使用 --clean 移除 DNS 确认不存在的域名规则。

依赖 dnspython。默认只报告；超时、无 A 记录和失效的别名目标均保留。
"""

import argparse
import concurrent.futures
import ipaddress
import os
from pathlib import Path

import dns.exception
import dns.name
import dns.rdatatype
import dns.resolver


BLACKLIST_FILE = Path("sources/ad-blacklist.txt")
MAX_WORKERS = 50
TIMEOUT = 2


def rule_domain(line):
    rule = line.strip()
    if not rule or rule.startswith(("#", "!", ";", "---")):
        return None
    if "," in rule:
        kind, value, *_ = rule.split(",")
        if kind.strip().upper() not in {"DOMAIN", "HOST", "DOMAIN-SUFFIX", "HOST-SUFFIX"}:
            return None
        rule = value.strip()
    domain = rule.removeprefix("*.").removeprefix(".").rstrip(".").lower()
    if "." not in domain or not all(c.isalnum() or c in ".-_" for c in domain):
        return None
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        return domain
    return None


def is_nonexistent(domain, resolver):
    """只接受原域名本身有 SOA 否定应答的 NXDOMAIN。"""
    try:
        qname = dns.name.from_text(domain)
        resolver.resolve(qname, "A", search=False, raise_on_no_answer=False, lifetime=TIMEOUT)
    except dns.resolver.NXDOMAIN as error:
        response = error.responses().get(qname)
        # 别名指向不存在的目标时，原域名仍然存在。
        if response is not None and not response.answer:
            return any(rrset.rdtype == dns.rdatatype.SOA for rrset in response.authority)
    except dns.exception.DNSException as error:
        print(f"  保留 {domain}（{type(error).__name__}）")
    return False


def check_blacklist(path, clean):
    original = path.read_bytes()
    lines = original.decode("utf-8").splitlines(keepends=True)
    domains = [rule_domain(line) for line in lines]
    unique = sorted(set(domains) - {None})
    resolver = dns.resolver.Resolver()
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(is_nonexistent, domain, resolver): domain for domain in unique}
        missing = {futures[f] for f in concurrent.futures.as_completed(futures) if f.result()}

    print(f"检查了 {len(unique)} 个域名，{len(missing)} 个返回 NXDOMAIN")
    for domain in sorted(missing):
        print(f"  {domain}")
    if not clean or not missing:
        return 0

    kept = [line for line, domain in zip(lines, domains) if domain not in missing]
    if path.read_bytes() != original:
        raise RuntimeError(f"{path} 在检查期间已修改，请重新运行")
    path.write_bytes("".join(kept).encode("utf-8"))
    removed = len(lines) - len(kept)
    print(f"已移除 {removed} 条规则")
    return removed


def main():
    parser = argparse.ArgumentParser(description="检查本地黑名单的 DNS 状态")
    parser.add_argument("--clean", action="store_true", help="移除已确认失效的域名规则")
    args = parser.parse_args()
    removed = check_blacklist(BLACKLIST_FILE, args.clean)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"invalid_count={removed}\n")


if __name__ == "__main__":
    main()
