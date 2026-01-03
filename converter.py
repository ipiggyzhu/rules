import requests
import os
import datetime
import time
import json

# ============================================================================
# 配置
# ============================================================================

# Loon 广告规则上游源
LOON_AD_RULES_URLS = [
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising.list",
    "https://raw.githubusercontent.com/privacy-protection-tools/anti-AD/master/anti-ad-surge.txt"
]

# Quantumult X 广告规则上游源
QUANTUMULTX_AD_RULES_URLS = [
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/Advertising/Advertising.list",
    "https://raw.githubusercontent.com/Cats-Team/AdRules/main/adrules.list",
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-QuantumultX.list",
    "https://raw.githubusercontent.com/limbopro/Adblock4limbo/main/rule/QuantumultX/Adblock4limbo.list"
]

# Loon 直连规则上游源
LOON_DIRECT_RULES_URLS = [
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/ChinaMax/ChinaMax.list"
]

# Quantumult X 直连规则上游源
QUANTUMULTX_DIRECT_RULES_URLS = [
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/ChinaMax/ChinaMax.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/ChinaMax/ChinaMax_No_IPv6.list"
]

# 路径配置
SOURCES_DIR = "sources"
BLACKLIST_FILE = os.path.join(SOURCES_DIR, "ad-blacklist.txt")
WHITELIST_FILE = os.path.join(SOURCES_DIR, "ad-whitelist.txt")

LOON_AD_OUTPUT = os.path.join("Loon", "ad-rules.list")
LOON_DIRECT_OUTPUT = os.path.join("Loon", "direct-rules.list")
QUANTUMULTX_AD_OUTPUT = os.path.join("QuantumultX", "ad-rules.list")
QUANTUMULTX_DIRECT_OUTPUT = os.path.join("QuantumultX", "direct-rules.list")

# 统计报告文件
STATS_FILE = "stats.json"

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒

# ============================================================================
# 统计类
# ============================================================================

class Stats:
    """统计收集器"""
    def __init__(self):
        self.source_stats = {}  # {url: count}
        self.failed_sources = []  # 失败的源
        self.before_dedup = {}  # {category: count}
        self.after_dedup = {}  # {category: count}
        self.final_counts = {}  # {output_file: count}

    def add_source(self, url, count, success=True):
        if success:
            self.source_stats[url] = count
        else:
            self.failed_sources.append(url)

    def set_dedup_stats(self, category, before, after):
        self.before_dedup[category] = before
        self.after_dedup[category] = after

    def set_final_count(self, output_file, count):
        self.final_counts[output_file] = count

    def get_diff(self):
        """与上次运行对比"""
        if not os.path.exists(STATS_FILE):
            return None

        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                old_stats = json.load(f)

            diff = {}
            for key, new_count in self.final_counts.items():
                old_count = old_stats.get('final_counts', {}).get(key, 0)
                diff[key] = new_count - old_count
            return diff
        except:
            return None

    def save(self):
        """保存统计到文件"""
        data = {
            'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'source_stats': self.source_stats,
            'failed_sources': self.failed_sources,
            'before_dedup': self.before_dedup,
            'after_dedup': self.after_dedup,
            'final_counts': self.final_counts
        }
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def print_report(self):
        """打印统计报告"""
        print("\n" + "=" * 60)
        print("📊 统计报告")
        print("=" * 60)

        # 各源贡献
        print("\n📥 各上游源贡献:")
        for url, count in self.source_stats.items():
            short_name = url.split('/')[-1][:40]
            print(f"  • {short_name}: {count} 条")

        # 失败的源
        if self.failed_sources:
            print("\n❌ 失败的源:")
            for url in self.failed_sources:
                short_name = url.split('/')[-1][:40]
                print(f"  • {short_name}")

        # 去重对比
        print("\n🔄 去重统计:")
        for category in self.before_dedup:
            before = self.before_dedup[category]
            after = self.after_dedup[category]
            removed = before - after
            print(f"  • {category}: {before} → {after} (去重 {removed} 条)")

        # 最终数量
        print("\n📁 最终输出:")
        for output_file, count in self.final_counts.items():
            print(f"  • {output_file}: {count} 条")

        # 与上次对比
        diff = self.get_diff()
        if diff:
            print("\n📈 与上次对比:")
            for output_file, change in diff.items():
                if change > 0:
                    print(f"  • {output_file}: +{change} 条")
                elif change < 0:
                    print(f"  • {output_file}: {change} 条")
                else:
                    print(f"  • {output_file}: 无变化")

# 全局统计实例
stats = Stats()

# ============================================================================
# 函数
# ============================================================================

def fetch_with_retry(url, max_retries=MAX_RETRIES):
    """带重试机制的请求"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                print(f"     ⚠️ 第 {attempt + 1} 次失败，{RETRY_DELAY}秒后重试...")
                time.sleep(RETRY_DELAY)
            else:
                raise e
    return None


def fetch_rules_from_urls(urls):
    """从多个URL获取规则"""
    rules = set()
    for url in urls:
        try:
            print(f"  📥 {url.split('/')[-1][:50]}")
            response = fetch_with_retry(url)
            count = 0
            for line in response.text.splitlines():
                line = line.strip()
                if line and not line.startswith(('!', '#', ';', '[')):
                    rules.add(line)
                    count += 1
            print(f"     ✅ 获取 {count} 条规则")
            stats.add_source(url, count, success=True)
        except requests.RequestException as e:
            print(f"     ❌ 失败: {e}")
            stats.add_source(url, 0, success=False)
    return rules


def load_local_rules(filepath, auto_prefix=True):
    """加载本地规则文件"""
    rules = set()
    if not os.path.exists(filepath):
        return rules

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith(('#', '!', ';', '---')):
                if auto_prefix and ',' not in line:
                    rules.add(f'DOMAIN-SUFFIX,{line}')
                else:
                    rules.add(line)
    return rules


def load_whitelist(filepath):
    """加载白名单（纯域名）"""
    domains = set()
    if not os.path.exists(filepath):
        return domains

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith(('#', '!', ';', '---')):
                # 处理完整规则格式 (HOST,domain,action)
                if ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        domains.add(parts[1].strip().lower())
                else:
                    domains.add(line.lower())
    return domains


def filter_by_whitelist(rules, whitelist):
    """根据白名单过滤规则"""
    if not whitelist:
        return rules

    filtered = set()
    removed_count = 0

    for rule in rules:
        parts = rule.split(',')
        if len(parts) >= 2:
            domain = parts[1].strip().lower()
            # 检查域名是否在白名单中，或者是白名单域名的子域名
            should_remove = False
            for white_domain in whitelist:
                if domain == white_domain or domain.endswith('.' + white_domain):
                    should_remove = True
                    break
            if should_remove:
                removed_count += 1
                continue
        filtered.add(rule)

    if removed_count > 0:
        print(f"  🛡️ 白名单过滤 {removed_count} 条规则")

    return filtered


def clean_rule_value(value):
    """清理规则值"""
    return value.lstrip('*./')


def remove_redundant_rules(rules):
    """
    移除被父域名覆盖的冗余子域名规则
    例如：如果存在 DOMAIN-SUFFIX,example.com，则 DOMAIN-SUFFIX,ad.example.com 是多余的
    """
    # 提取所有 SUFFIX 类型的域名
    suffix_domains = set()
    for rule in rules:
        parts = rule.split(',')
        if len(parts) >= 2:
            rule_type = parts[0].upper()
            if rule_type in ('DOMAIN-SUFFIX', 'HOST-SUFFIX'):
                suffix_domains.add(parts[1].lower())

    # 找出被覆盖的子域名
    redundant = set()
    for domain in suffix_domains:
        # 检查是否有父域名存在
        parts = domain.split('.')
        for i in range(1, len(parts)):
            parent = '.'.join(parts[i:])
            if parent in suffix_domains:
                redundant.add(domain)
                break

    # 过滤掉冗余规则
    filtered = []
    removed_count = 0
    for rule in rules:
        parts = rule.split(',')
        if len(parts) >= 2:
            rule_type = parts[0].upper()
            rule_value = parts[1].lower()
            if rule_type in ('DOMAIN-SUFFIX', 'HOST-SUFFIX') and rule_value in redundant:
                removed_count += 1
                continue
        filtered.append(rule)

    if removed_count > 0:
        print(f"     🧹 移除 {removed_count} 条冗余子域名规则")

    return filtered


def format_for_loon(rules):
    """格式化为 Loon 格式"""
    formatted = set()
    domain_types = ('HOST-SUFFIX', 'DOMAIN-SUFFIX', 'HOST-KEYWORD', 'DOMAIN-KEYWORD', 'HOST', 'DOMAIN')

    for rule in rules:
        parts = [p.strip() for p in rule.split(',')]
        if len(parts) < 2:
            continue

        rule_type = parts[0].upper()
        rule_value = clean_rule_value(parts[1])
        if not rule_value:
            continue

        if rule_type in domain_types and '/' in rule_value:
            continue

        if rule_type in ('HOST-SUFFIX', 'DOMAIN-SUFFIX'):
            formatted.add(f'DOMAIN-SUFFIX,{rule_value}')
        elif rule_type in ('HOST-KEYWORD', 'DOMAIN-KEYWORD'):
            formatted.add(f'DOMAIN-KEYWORD,{rule_value}')
        elif rule_type in ('HOST', 'DOMAIN'):
            formatted.add(f'DOMAIN,{rule_value}')
        elif rule_type == 'IP-CIDR' and '/' in rule_value:
            formatted.add(f'IP-CIDR,{rule_value},no-resolve')
        elif rule_type == 'IP-CIDR6' and '/' in rule_value:
            formatted.add(f'IP-CIDR6,{rule_value},no-resolve')
        elif rule_type in ('USER-AGENT', 'URL-REGEX'):
            formatted.add(f'{rule_type},{parts[1]}')

    # 移除冗余子域名规则
    result = remove_redundant_rules(sorted(formatted))
    return result


def format_for_quantumultx(rules):
    """格式化为 Quantumult X 格式"""
    formatted = set()
    domain_types = ('HOST-SUFFIX', 'DOMAIN-SUFFIX', 'HOST-KEYWORD', 'DOMAIN-KEYWORD', 'HOST', 'DOMAIN')

    for rule in rules:
        parts = [p.strip() for p in rule.split(',')]
        if len(parts) < 2:
            continue

        rule_type = parts[0].upper()
        rule_value = clean_rule_value(parts[1])
        if not rule_value:
            continue

        if rule_type in domain_types and '/' in rule_value:
            continue

        if rule_type in ('DOMAIN-SUFFIX', 'HOST-SUFFIX'):
            formatted.add(f'HOST-SUFFIX,{rule_value}')
        elif rule_type in ('DOMAIN-KEYWORD', 'HOST-KEYWORD'):
            formatted.add(f'HOST-KEYWORD,{rule_value}')
        elif rule_type in ('DOMAIN', 'HOST'):
            formatted.add(f'HOST,{rule_value}')
        elif rule_type == 'IP-CIDR' and '/' in rule_value:
            formatted.add(f'IP-CIDR,{rule_value},no-resolve')
        elif rule_type == 'IP-CIDR6' and '/' in rule_value:
            formatted.add(f'IP-CIDR6,{rule_value},no-resolve')
        elif rule_type in ('USER-AGENT', 'URL-REGEX'):
            formatted.add(f'{rule_type},{parts[1]}')

    # 移除冗余子域名规则
    result = remove_redundant_rules(sorted(formatted))
    return result


def write_rules(filepath, rules, title):
    """写入规则文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Title: {title}\n")
        f.write(f"# Description: Auto-generated. Do not edit manually.\n")
        f.write(f"# Updated: {timestamp}\n")
        f.write(f"# Total: {len(rules)}\n\n")
        for rule in rules:
            f.write(f"{rule}\n")

    print(f"  ✅ {filepath} ({len(rules)} 条规则)")
    stats.set_final_count(filepath, len(rules))


def generate_summary():
    """生成用于 commit message 的摘要"""
    diff = stats.get_diff()
    lines = []

    for output_file, count in stats.final_counts.items():
        change = ""
        if diff and output_file in diff:
            d = diff[output_file]
            if d > 0:
                change = f" (+{d})"
            elif d < 0:
                change = f" ({d})"
        lines.append(f"{os.path.basename(output_file)}: {count}{change}")

    return " | ".join(lines)


# ============================================================================
# 主程序
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 规则聚合脚本")
    print("=" * 60)

    # 加载本地源文件
    print("\n📂 加载本地源文件...")
    blacklist = load_local_rules(BLACKLIST_FILE)
    whitelist = load_whitelist(WHITELIST_FILE)
    print(f"  黑名单: {len(blacklist)} 条")
    print(f"  白名单: {len(whitelist)} 条")

    # ========== 广告规则 ==========

    # 生成 Loon 广告规则
    print("\n🍎 生成 Loon 广告规则...")
    loon_ad_upstream = fetch_rules_from_urls(LOON_AD_RULES_URLS)
    loon_ad_combined = loon_ad_upstream | blacklist
    stats.set_dedup_stats("Loon广告规则", len(loon_ad_combined), len(loon_ad_combined))
    loon_ad_filtered = filter_by_whitelist(loon_ad_combined, whitelist)
    loon_ad_final = format_for_loon(loon_ad_filtered)
    stats.set_dedup_stats("Loon广告规则", len(loon_ad_combined), len(loon_ad_final))
    write_rules(LOON_AD_OUTPUT, loon_ad_final, "Loon Ad Rules")

    # 生成 Quantumult X 广告规则
    print("\n🔷 生成 Quantumult X 广告规则...")
    qx_ad_upstream = fetch_rules_from_urls(QUANTUMULTX_AD_RULES_URLS)
    qx_ad_combined = qx_ad_upstream | blacklist
    qx_ad_filtered = filter_by_whitelist(qx_ad_combined, whitelist)
    qx_ad_final = format_for_quantumultx(qx_ad_filtered)
    stats.set_dedup_stats("QX广告规则", len(qx_ad_combined), len(qx_ad_final))
    write_rules(QUANTUMULTX_AD_OUTPUT, qx_ad_final, "QuantumultX Ad Rules")

    # ========== 直连规则 ==========

    # 生成 Loon 直连规则
    print("\n🍎 生成 Loon 直连规则...")
    loon_direct_upstream = fetch_rules_from_urls(LOON_DIRECT_RULES_URLS)
    loon_direct_final = format_for_loon(loon_direct_upstream)
    stats.set_dedup_stats("Loon直连规则", len(loon_direct_upstream), len(loon_direct_final))
    write_rules(LOON_DIRECT_OUTPUT, loon_direct_final, "Loon Direct Rules")

    # 生成 Quantumult X 直连规则
    print("\n🔷 生成 Quantumult X 直连规则...")
    qx_direct_upstream = fetch_rules_from_urls(QUANTUMULTX_DIRECT_RULES_URLS)
    qx_direct_final = format_for_quantumultx(qx_direct_upstream)
    stats.set_dedup_stats("QX直连规则", len(qx_direct_upstream), len(qx_direct_final))
    write_rules(QUANTUMULTX_DIRECT_OUTPUT, qx_direct_final, "QuantumultX Direct Rules")

    # 打印统计报告
    stats.print_report()

    # 保存统计数据
    stats.save()

    # 输出摘要（供 GitHub Actions 使用）
    summary = generate_summary()
    print(f"\n📝 摘要: {summary}")

    # 保存失效的上游源到文件供 Telegram 通知使用
    if stats.failed_sources:
        with open("failed_sources.txt", "w", encoding="utf-8") as f:
            for url in stats.failed_sources:
                f.write(f"{url}\n")

    # 写入环境变量文件（供 GitHub Actions 读取）
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        # 计算总去重数量
        total_dedup = sum(stats.before_dedup[k] - stats.after_dedup[k] for k in stats.before_dedup)
        with open(github_output, 'a') as f:
            f.write(f"summary={summary}\n")
            f.write(f"has_failed={'true' if stats.failed_sources else 'false'}\n")
            f.write(f"failed_count={len(stats.failed_sources)}\n")
            f.write(f"dedup_count={total_dedup}\n")
            # 添加各个规则文件的数量
            f.write(f"loon_ad_count={stats.final_counts.get(LOON_AD_OUTPUT, 0)}\n")
            f.write(f"loon_direct_count={stats.final_counts.get(LOON_DIRECT_OUTPUT, 0)}\n")
            f.write(f"qx_ad_count={stats.final_counts.get(QUANTUMULTX_AD_OUTPUT, 0)}\n")
            f.write(f"qx_direct_count={stats.final_counts.get(QUANTUMULTX_DIRECT_OUTPUT, 0)}\n")

    print("\n" + "=" * 60)
    print("✅ 完成!")
    print("=" * 60)
