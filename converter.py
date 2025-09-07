import requests
import os
import datetime

# --- 配置 ---
# 统一的广告规则来源
AD_RULES_URLS = [
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising.list",
    "https://raw.githubusercontent.com/privacy-protection-tools/anti-AD/master/anti-ad-loon.txt",
    "https://raw.githubusercontent.com/Cats-Team/AdRules/main/qx.conf",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/PCDN/PCDN.list"
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
    """为Loon格式化规则，并进行严格的格式清理和统一。"""
    formatted_rules = set()  # 使用集合以自动处理转换后的重复项
    for rule in raw_rules:
        parts = [p.strip() for p in rule.split(',')]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            continue

        rule_type = parts[0].upper()
        rule_value = parts[1]

        # 将 QX 的 HOST-* 格式和 Loon 的 DOMAIN-* 格式统一为 Loon 标准格式
        if rule_type in ('HOST-SUFFIX', 'DOMAIN-SUFFIX'):
            formatted_rules.add(f'DOMAIN-SUFFIX,{rule_value}')
        elif rule_type in ('HOST-KEYWORD', 'DOMAIN-KEYWORD'):
            formatted_rules.add(f'DOMAIN-KEYWORD,{rule_value}')
        elif rule_type in ('HOST', 'DOMAIN'):
            formatted_rules.add(f'DOMAIN,{rule_value}')
        elif rule_type == 'IP-CIDR':
            # 验证IP-CIDR格式 (支持IPv4和IPv6)
            if '/' in rule_value and ('.' in rule_value or ':' in rule_value):
                formatted_rules.add(f'IP-CIDR,{rule_value}')
        # 保留其他Loon兼容的规则类型
        elif rule_type in ('USER-AGENT', 'URL-REGEX'):
            formatted_rules.add(f'{rule_type},{rule_value}')
            
    return sorted(list(formatted_rules))

def format_for_quantumultx(raw_rules):
    """为QuantumultX格式化规则，并进行严格的格式清理。"""
    formatted_rules = set() # 使用集合以自动处理转换后的重复项
    for rule in raw_rules:
        parts = [p.strip() for p in rule.split(',')]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            continue

        rule_type = parts[0].upper()
        rule_value = parts[1]

        # 将 Loon 的 DOMAIN-* 格式和 QX 的 HOST-* 格式统一为 QX 标准格式
        if rule_type in ('DOMAIN-SUFFIX', 'HOST-SUFFIX'):
            formatted_rules.add(f'HOST-SUFFIX,{rule_value}')
        elif rule_type in ('DOMAIN-KEYWORD', 'HOST-KEYWORD'):
            formatted_rules.add(f'HOST-KEYWORD,{rule_value}')
        elif rule_type in ('DOMAIN', 'HOST'):
            formatted_rules.add(f'HOST,{rule_value}')
        elif rule_type == 'IP-CIDR':
            # 验证IP-CIDR格式 (支持IPv4和IPv6)
            if '/' in rule_value and ('.' in rule_value or ':' in rule_value):
                formatted_rules.add(f'IP-CIDR,{rule_value}')
        # 保留其他QX兼容的规则类型
        elif rule_type in ('USER-AGENT', 'URL-REGEX'):
            formatted_rules.add(f'{rule_type},{rule_value}')
                
    return sorted(list(formatted_rules))

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

# --- 主逻辑 ---

if __name__ == "__main__":
    print("--- Starting Ad Rule Aggregation ---")
    
    # 1. 获取并合并所有广告规则源
    print("\nFetching ad rule lists...")
    master_ad_rules = sorted(list(fetch_raw_rules(AD_RULES_URLS)))
    
    # 2. 合并手动添加的黑名单规则
    manual_reject_path = os.path.join("manual", "reject-rules.txt")
    manual_reject_rules = fetch_manual_reject_rules(manual_reject_path)
    master_ad_rules = sorted(list(set(master_ad_rules) | set(manual_reject_rules)))
    
    # 3. 移除手动添加的白名单规则
    manual_allow_path = os.path.join("manual", "allow-rules.txt")
    manual_allow_rules = fetch_manual_allow_rules(manual_allow_path)
    master_ad_rules = sorted(list(set(master_ad_rules) - set(manual_allow_rules)))

    print(f"Found {len(master_ad_rules)} unique ad rules after deduplication and manual adjustments.")

    # 4. 生成Loon.list文件
    print("\n--- Generating .list Rules for Loon ---")
    loon_ad_rules = format_for_loon(master_ad_rules)
    write_rules_to_file(
        os.path.join(LOON_OUTPUT_DIR, "ad-rules.list"), 
        loon_ad_rules, 
        "Loon Ad Rules (Aggregated)"
    )

    # 5. 生成QuantumultX.list文件
    print("\n--- Generating .list Rules for QuantumultX ---")
    q_ad_rules = format_for_quantumultx(master_ad_rules)
    write_rules_to_file(
        os.path.join(QUANTUMULTX_OUTPUT_DIR, "ad-rules.list"),
        q_ad_rules,
        "QuantumultX Ad Rules (Aggregated)"
    )
    
    print("\n--- Ad Rule Aggregation Finished ---")
