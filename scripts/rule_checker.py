"""
规则有效性检查器

功能：检查黑名单中的域名是否仍然有效（能够解析）
用途：定期清理无效/过期的域名规则

使用方法：
    python scripts/rule_checker.py [--clean]

参数：
    --clean: 自动移除无效域名（默认只报告）
"""

import os
import socket
import concurrent.futures
from typing import Set, Tuple
import argparse

# 配置
SOURCES_DIR = 'sources'
BLACKLIST_FILE = os.path.join(SOURCES_DIR, 'ad-blacklist.txt')
MAX_WORKERS = 50  # 并发检查数
TIMEOUT = 2  # DNS 解析超时（秒）


def load_domains() -> Tuple[list, Set[str]]:
    """加载黑名单域名，返回 (注释行, 域名集合)"""
    comments = []
    domains = set()

    if not os.path.exists(BLACKLIST_FILE):
        print(f"文件不存在: {BLACKLIST_FILE}")
        return comments, domains

    with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith(('#', '!', ';', '---')):
                comments.append(line)
            else:
                domains.add(line)

    return comments, domains


def check_domain(domain: str) -> Tuple[str, bool, str]:
    """
    检查域名是否可解析
    返回: (域名, 是否有效, 原因)
    """
    try:
        socket.setdefaulttimeout(TIMEOUT)
        socket.gethostbyname(domain)
        return (domain, True, "OK")
    except socket.gaierror as e:
        # 常见错误码
        if e.errno == socket.EAI_NONAME:
            return (domain, False, "域名不存在")
        elif e.errno == socket.EAI_AGAIN:
            return (domain, True, "DNS 临时失败（保留）")
        else:
            return (domain, False, f"DNS 错误: {e}")
    except socket.timeout:
        return (domain, True, "超时（保留）")
    except Exception as e:
        return (domain, True, f"未知错误（保留）: {e}")


def check_all_domains(domains: Set[str]) -> Tuple[Set[str], Set[str]]:
    """
    并发检查所有域名
    返回: (有效域名, 无效域名)
    """
    valid = set()
    invalid = set()

    total = len(domains)
    print(f"\n检查 {total} 个域名...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_domain, d): d for d in domains}

        done = 0
        for future in concurrent.futures.as_completed(futures):
            domain, is_valid, reason = future.result()
            done += 1

            if is_valid:
                valid.add(domain)
            else:
                invalid.add(domain)
                print(f"  ❌ {domain} - {reason}")

            # 进度显示
            if done % 100 == 0 or done == total:
                print(f"  进度: {done}/{total} ({done*100//total}%)")

    return valid, invalid


def save_blacklist(comments: list, domains: Set[str]):
    """保存黑名单"""
    with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
        # 写入注释
        for line in comments:
            f.write(f"{line}\n")
        if comments:
            f.write("\n")

        # 写入域名（排序）
        for domain in sorted(domains):
            f.write(f"{domain}\n")


def main():
    parser = argparse.ArgumentParser(description='检查规则有效性')
    parser.add_argument('--clean', action='store_true', help='自动移除无效域名')
    args = parser.parse_args()

    print("=" * 60)
    print("📋 规则有效性检查器")
    print("=" * 60)

    # 加载域名
    comments, domains = load_domains()
    print(f"\n已加载 {len(domains)} 个域名")

    if not domains:
        print("没有域名需要检查")
        return

    # 检查域名
    valid, invalid = check_all_domains(domains)

    # 报告
    print("\n" + "=" * 60)
    print("📊 检查结果")
    print("=" * 60)
    print(f"  有效: {len(valid)} 个")
    print(f"  无效: {len(invalid)} 个")

    if invalid:
        print(f"\n无效域名列表:")
        for domain in sorted(invalid)[:50]:
            print(f"  • {domain}")
        if len(invalid) > 50:
            print(f"  ... 等共 {len(invalid)} 个")

        if args.clean:
            print(f"\n🧹 清理无效域名...")
            save_blacklist(comments, valid)
            print(f"  已移除 {len(invalid)} 个无效域名")
            print(f"  剩余 {len(valid)} 个有效域名")
        else:
            print(f"\n💡 提示: 使用 --clean 参数自动移除无效域名")
    else:
        print("\n✅ 所有域名都有效!")

    print("\n" + "=" * 60)
    print("检查完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
