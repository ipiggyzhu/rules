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
    "https://raw.githubusercontent.com/sooyaaabo/Loon/main/Rule/AdRules.list"
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
    # 在这里，我们假设原始规则大部分兼容Loon，所以不做大的改动
    return raw_rules

def format_for_quantumultx(raw_rules):
    """为QuantumultX格式化规则。"""
    formatted_rules = []
    for rule in raw_rules:
        # 示例：将 DOMAIN-SUFFIX 转换为 HOST-SUFFIX
        if 'DOMAIN-SUFFIX' in rule:
            formatted_rules.append(rule.replace('DOMAIN-SUFFIX', 'HOST-SUFFIX'))
        # 示例：将 DOMAIN-KEYWORD 转换为 HOST-KEYWORD
        elif 'DOMAIN-KEYWORD' in rule:
            formatted_rules.append(rule.replace('DOMAIN-KEYWORD', 'HOST-KEYWORD'))
        # 其他类型的规则可以保留或根据需要转换
        else:
            formatted_rules.append(rule)
    return formatted_rules

def write_rules_to_file(filepath, rules, title):
    """将规则列表写入文件，并添加文件头。"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    # 获取当前UTC时间
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    # 格式化为ISO 8601格式
    timestamp = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"! Title: {title}\n")
        f.write(f"! Description: Generated from multiple sources. Do not edit manually.\n")
        f.write(f"! Last Updated: {timestamp}\n")
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

# --- 主逻辑 ---

if __name__ == "__main__":
    print("--- Starting Unified Rule Conversion ---")

    # 1. 获取统一的广告和直连规则
    print("\nFetching master rule lists...")
    master_ad_rules = sorted(list(fetch_raw_rules(AD_RULES_URLS)))
    master_direct_rules = sorted(list(fetch_raw_rules(DIRECT_RULES_URLS)))
    # 读取manual黑名单并合并到广告规则
    manual_reject_path = os.path.join("manual", "reject-rules.txt")
    manual_reject_rules = fetch_manual_reject_rules(manual_reject_path)
    master_ad_rules = sorted(list(set(master_ad_rules) | set(manual_reject_rules)))
    # 读取manual白名单并从广告规则中排除
    manual_allow_path = os.path.join("manual", "allow-rules.txt")
    manual_allow_rules = fetch_manual_allow_rules(manual_allow_path)
    master_ad_rules = sorted(list(set(master_ad_rules) - set(manual_allow_rules)))
    print(f"Found {len(master_ad_rules)} unique ad rules and {len(master_direct_rules)} unique direct rules after exact deduplication and allowlist exclusion.")

    # 2. 为Loon生成规则文件
    print("\n--- Generating Rules for Loon ---")
    loon_ad_rules = format_for_loon(master_ad_rules)
    write_rules_to_file(
        os.path.join(LOON_OUTPUT_DIR, "ad-rules.txt"), 
        loon_ad_rules, 
        "Loon Ad Rules (Aggregated)"
    )
    
    loon_direct_rules = format_for_loon(master_direct_rules)
    write_rules_to_file(
        os.path.join(LOON_OUTPUT_DIR, "direct-rules.txt"),
        loon_direct_rules,
        "Loon Direct Rules (Aggregated)"
    )

    # 3. 为QuantumultX生成规则文件
    print("\n--- Generating Rules for QuantumultX ---")
    q_ad_rules = format_for_quantumultx(master_ad_rules)
    write_rules_to_file(
        os.path.join(QUANTUMULTX_OUTPUT_DIR, "ad-rules.txt"),
        q_ad_rules,
        "QuantumultX Ad Rules (Aggregated)"
    )
    
    q_direct_rules = format_for_quantumultx(master_direct_rules)
    write_rules_to_file(
        os.path.join(QUANTUMULTX_OUTPUT_DIR, "direct-rules.txt"),
        q_direct_rules,
        "QuantumultX Direct Rules (Aggregated)"
    )

    print("\n--- Unified Rule Conversion Finished ---")