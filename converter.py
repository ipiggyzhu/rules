import requests
import os
import datetime

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
    "https://raw.githubusercontent.com/Cats-Team/AdRules/main/qx.conf"
]

# Loon 直连规则上游源
LOON_DIRECT_RULES_URLS = [
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/ChinaMax/ChinaMax.list"
]

# Quantumult X 直连规则上游源
QUANTUMULTX_DIRECT_RULES_URLS = [
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/ChinaMax/ChinaMax.list"
]

# 路径配置
SOURCES_DIR = "sources"
BLACKLIST_FILE = os.path.join(SOURCES_DIR, "ad-blacklist.txt")
WHITELIST_FILE = os.path.join(SOURCES_DIR, "ad-whitelist.txt")

LOON_AD_OUTPUT = os.path.join("Loon", "ad-rules.list")
LOON_DIRECT_OUTPUT = os.path.join("Loon", "direct-rules.list")
QUANTUMULTX_AD_OUTPUT = os.path.join("QuantumultX", "ad-rules.list")
QUANTUMULTX_DIRECT_OUTPUT = os.path.join("QuantumultX", "direct-rules.list")

# ============================================================================
# 函数
# ============================================================================

def fetch_rules_from_urls(urls):
    """从多个URL获取规则"""
    rules = set()
    for url in urls:
        try:
            print(f"  📥 {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            for line in response.text.splitlines():
                line = line.strip()
                if line and not line.startswith(('!', '#', ';')):
                    rules.add(line)
            print(f"     获取 {len(response.text.splitlines())} 行")
        except requests.RequestException as e:
            print(f"  ❌ 失败: {e}")
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
                domains.add(line)
    return domains


def clean_rule_value(value):
    """清理规则值"""
    return value.lstrip('*./')


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
            formatted.add(f'IP-CIDR,{rule_value}')
        elif rule_type == 'IP-CIDR6' and '/' in rule_value:
            formatted.add(f'IP-CIDR6,{rule_value}')
        elif rule_type in ('USER-AGENT', 'URL-REGEX'):
            formatted.add(f'{rule_type},{parts[1]}')

    return sorted(formatted)


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
            formatted.add(f'IP-CIDR,{rule_value}')
        elif rule_type == 'IP-CIDR6' and '/' in rule_value:
            formatted.add(f'IP-CIDR6,{rule_value}')
        elif rule_type in ('USER-AGENT', 'URL-REGEX'):
            formatted.add(f'{rule_type},{parts[1]}')

    return sorted(formatted)


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
    loon_ad_filtered = loon_ad_combined - whitelist
    loon_ad_final = format_for_loon(loon_ad_filtered)
    write_rules(LOON_AD_OUTPUT, loon_ad_final, "Loon Ad Rules")

    # 生成 Quantumult X 广告规则
    print("\n🔷 生成 Quantumult X 广告规则...")
    qx_ad_upstream = fetch_rules_from_urls(QUANTUMULTX_AD_RULES_URLS)
    qx_ad_combined = qx_ad_upstream | blacklist
    qx_ad_filtered = qx_ad_combined - whitelist
    qx_ad_final = format_for_quantumultx(qx_ad_filtered)
    write_rules(QUANTUMULTX_AD_OUTPUT, qx_ad_final, "QuantumultX Ad Rules")

    # ========== 直连规则 ==========

    # 生成 Loon 直连规则
    print("\n🍎 生成 Loon 直连规则...")
    loon_direct_upstream = fetch_rules_from_urls(LOON_DIRECT_RULES_URLS)
    loon_direct_final = format_for_loon(loon_direct_upstream)
    write_rules(LOON_DIRECT_OUTPUT, loon_direct_final, "Loon Direct Rules")

    # 生成 Quantumult X 直连规则
    print("\n🔷 生成 Quantumult X 直连规则...")
    qx_direct_upstream = fetch_rules_from_urls(QUANTUMULTX_DIRECT_RULES_URLS)
    qx_direct_final = format_for_quantumultx(qx_direct_upstream)
    write_rules(QUANTUMULTX_DIRECT_OUTPUT, qx_direct_final, "QuantumultX Direct Rules")

    print("\n" + "=" * 60)
    print("✅ 完成!")
    print("=" * 60)
