import requests
import os
import datetime

# --- 配置 ---
# 统一的规则来源
AD_RULES_URLS = [
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising.list",
    "https://raw.githubusercontent.com/sooyaaabo/Loon/main/Rule/PCDN.list",
    "https://raw.githubusercontent.com/sooyaaabo/Loon/main/Rule/MyBlockAds.list",
    "https://raw.githubusercontent.com/sooyaaabo/Loon/main/Rule/RejectAd.list",
    "https://raw.githubusercontent.com/sooyaaabo/Loon/main/Rule/AdRules.list",
    "https://raw.githubusercontent.com/Cats-Team/AdRules/main/qx.conf"
]

DIRECT_RULES_URLS = [
    "https://raw.githubusercontent.com/sooyaaabo/Loon/main/Rule/Apple.list",
    "https://raw.githubusercontent.com/sooyaaabo/Loon/main/Rule/Media-Direct",
    "https://raw.githubusercontent.com/sooyaaabo/Loon/main/Rule/Media-Proxy.list",
    "https://raw.githubusercontent.com/sooyaaabo/KeleeOne/Loon/Rule/ChinaMax.list",
    "https://raw.githubusercontent.com/sooyaaabo/Loon/main/Rule/Lan",
    "https://raw.githubusercontent.com/sooyaaabo/Loon/main/Rule/CN_REGION"
]

# 输出目录
LOON_OUTPUT_DIR = "Loon"
QUANTUMULTX_OUTPUT_DIR = "QuantumultX"

# --- 函数 ---

def fetch_raw_rules(urls):
    """从URL列表中获取原始规则行，并进行精确去重。"""
    raw_lines = set()
    for url in urls:
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            lines = response.text.splitlines()
            for line in lines:
                # 仅处理有效行
                if line.strip() and not line.strip().startswith(('!', '#', ';')):
                    raw_lines.add(line.strip())
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
    return sorted(list(raw_lines))

def format_for_loon(raw_rules):
    """为Loon格式化规则。Loon通常可以直接使用DOMAIN-SUFFIX等。"""
    return raw_rules

def format_for_quantumultx(raw_rules):
    """为QuantumultX格式化规则，并进行严格的格式清理。"""
    formatted_rules = []
    for rule in raw_rules:
        parts = [p.strip() for p in rule.split(',')]
        if not parts:
            continue

        rule_type = parts[0].upper()
        rule_value = parts[1] if len(parts) > 1 else ''

        if not rule_value: 
            continue

        if rule_type == 'DOMAIN-SUFFIX':
            formatted_rules.append(f'HOST-SUFFIX,{rule_value}')
        elif rule_type == 'DOMAIN-KEYWORD':
            formatted_rules.append(f'HOST-KEYWORD,{rule_value}')
        elif rule_type == 'DOMAIN':
            formatted_rules.append(f'HOST,{rule_value}')
        elif rule_type == 'IP-CIDR':
            # 验证IP-CIDR格式
            if '/' in rule_value and '.' in rule_value:
                formatted_rules.append(f'IP-CIDR,{rule_value}')
        # 其他规则类型，如果QuantumultX支持，则直接添加
        # 例如 USER-AGENT, URL-REGEX 等
        # 如果不确定，可以添加一个默认的大小写转换或直接保留
        else:
            # 保留原始格式，但确保类型和值之间只有一个逗号
            formatted_rules.append(f'{rule_type},{rule_value}')
                
    return formatted_rules

def write_rules_to_file(filepath, rules, title):
    """将规则列表写入文件，并添加文件头。"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    timestamp = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Title: {title}\n")
        f.write(f"# Description: Generated from multiple sources. Do not edit manually.\n")
        f.write(f"# Last Updated: {timestamp}\n")
        f.write("\n")
        for rule in rules:
            f.write(f"{rule}\n")
    print(f"✅ Successfully generated {filepath}")

def fetch_manual_reject_rules(filepath):
    """从本地manual/reject-rules.txt读取黑名单域名，返回域名列表。"""
    manual_rules = set()
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(('#', '!', ';')):
                    manual_rules.add(line)
    return sorted(list(manual_rules))

def fetch_manual_allow_rules(filepath):
    """从本地manual/allow-rules.txt读取白名单域名，返回域名列表。"""
    allow_rules = set()
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(('#', '!', ';', '---')):
                    allow_rules.add(line)
    return sorted(list(allow_rules))

def fetch_exclude_rules(filepath):
    """从本地manual/exclude-rules.txt读取要排除的域名，返回域名列表。"""
    exclude_rules = set()
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(('#', '!', ';')):
                    exclude_rules.add(line)
    return sorted(list(exclude_rules))

# --- 主逻辑 ---

if __name__ == "__main__":
    print("--- Starting Unified Rule Conversion ---")
    print("\nFetching master rule lists...")
    master_ad_rules = sorted(list(fetch_raw_rules(AD_RULES_URLS)))
    master_direct_rules = sorted(list(fetch_raw_rules(DIRECT_RULES_URLS)))
    manual_reject_path = os.path.join("manual", "reject-rules.txt")
    manual_reject_rules = fetch_manual_reject_rules(manual_reject_path)
    master_ad_rules = sorted(list(set(master_ad_rules) | set(manual_reject_rules)))
    manual_allow_path = os.path.join("manual", "allow-rules.txt")
    manual_allow_rules = fetch_manual_allow_rules(manual_allow_path)
    master_ad_rules = sorted(list(set(master_ad_rules) - set(manual_allow_rules)))

    # 读取排除规则并从直连规则中移除
    exclude_rules_path = os.path.join("manual", "exclude-rules.txt")
    exclude_rules = fetch_exclude_rules(exclude_rules_path)
    if exclude_rules:
        master_direct_rules = [rule for rule in master_direct_rules if rule.split(',')[-1].strip() not in exclude_rules]

    print(f"Found {len(master_ad_rules)} unique ad rules and {len(master_direct_rules)} unique direct rules after exact deduplication and allowlist exclusion.")

    # 生成Loon .list文件
    print("\n--- Generating .list Rules for Loon ---")
    loon_ad_rules = format_for_loon(master_ad_rules)
    write_rules_to_file(
        os.path.join(LOON_OUTPUT_DIR, "ad-rules.list"), 
        loon_ad_rules, 
        "Loon Ad Rules (Aggregated)"
    )
    loon_direct_rules = format_for_loon(master_direct_rules)
    write_rules_to_file(
        os.path.join(LOON_OUTPUT_DIR, "direct-rules.list"),
        loon_direct_rules,
        "Loon Direct Rules (Aggregated)"
    )

    # 生成QuantumultX .list文件
    print("\n--- Generating .list Rules for QuantumultX ---")
    q_ad_rules = format_for_quantumultx(master_ad_rules)
    write_rules_to_file(
        os.path.join(QUANTUMULTX_OUTPUT_DIR, "ad-rules.list"),
        q_ad_rules,
        "QuantumultX Ad Rules (Aggregated)"
    )
    q_direct_rules = format_for_quantumultx(master_direct_rules)
    write_rules_to_file(
        os.path.join(QUANTUMULTX_OUTPUT_DIR, "direct-rules.list"),
        q_direct_rules,
        "QuantumultX Direct Rules (Aggregated)"
    )
    print("\n--- Unified Rule Conversion Finished ---")