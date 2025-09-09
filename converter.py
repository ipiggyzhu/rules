import requests
import os
import datetime

# --- 配置 ---
# 1. Loon 专用的广告规则来源
LOON_AD_RULES_URLS = [
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising.list",
    "https://raw.githubusercontent.com/privacy-protection-tools/anti-AD/master/anti-ad-loon.txt",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/PCDN/PCDN.list"
]

# 2. Quantumult X 专用的广告规则来源
QUANTUMULTX_AD_RULES_URLS = [
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/Advertising/Advertising.list",
    "https://raw.githubusercontent.com/Cats-Team/AdRules/main/qx.conf",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/PCDN/PCDN.list"
]

# 输出目录
LOON_OUTPUT_DIR = "Loon"
QUANTUMULTX_OUTPUT_DIR = "QuantumultX"

# --- 函数 ---

def fetch_raw_rules(urls):
    """从URL列表中获取原始规则行。"""
    raw_lines = set()
    for url in urls:
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            lines = response.text.splitlines()
            for line in lines:
                if line.strip() and not line.strip().startswith(('!', '#', ';')):
                    raw_lines.add(line.strip())
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
    return raw_lines

def clean_rule_value(value):
    """清洗规则值，移除开头可能存在的非法字符，如 '*' 或 '.'"""
    if value.startswith(('*', '.')):
        return value.lstrip('*.')
    return value

def format_for_loon(raw_rules):
    """为Loon格式化规则，并进行严格的格式清理和统一。"""
    formatted_rules = set()
    for rule in raw_rules:
        parts = [p.strip() for p in rule.split(',')]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            continue
        rule_type = parts[0].upper()
        rule_value = clean_rule_value(parts[1]) # 清洗规则值
        if not rule_value: continue

        if rule_type in ('HOST-SUFFIX', 'DOMAIN-SUFFIX'):
            formatted_rules.add(f'DOMAIN-SUFFIX,{rule_value}')
        elif rule_type in ('HOST-KEYWORD', 'DOMAIN-KEYWORD'):
            formatted_rules.add(f'DOMAIN-KEYWORD,{rule_value}')
        elif rule_type in ('HOST', 'DOMAIN'):
            formatted_rules.add(f'DOMAIN,{rule_value}')
        elif rule_type == 'IP-CIDR':
            if '/' in rule_value and ('.' in rule_value or ':' in rule_value):
                formatted_rules.add(f'IP-CIDR,{rule_value}')
        elif rule_type in ('USER-AGENT', 'URL-REGEX'):
            formatted_rules.add(f'{rule_type},{rule_value}')
    return sorted(list(formatted_rules))

def format_for_quantumultx(raw_rules):
    """为QuantumultX格式化规则，并进行严格的格式清理。"""
    formatted_rules = set()
    for rule in raw_rules:
        parts = [p.strip() for p in rule.split(',')]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            continue
        rule_type = parts[0].upper()
        rule_value = clean_rule_value(parts[1]) # 清洗规则值
        if not rule_value: continue

        if rule_type in ('DOMAIN-SUFFIX', 'HOST-SUFFIX'):
            formatted_rules.add(f'HOST-SUFFIX,{rule_value}')
        elif rule_type in ('DOMAIN-KEYWORD', 'HOST-KEYWORD'):
            formatted_rules.add(f'HOST-KEYWORD,{rule_value}')
        elif rule_type in ('DOMAIN', 'HOST'):
            formatted_rules.add(f'HOST,{rule_value}')
        elif rule_type == 'IP-CIDR':
            if '/' in rule_value and ('.' in rule_value or ':' in rule_value):
                formatted_rules.add(f'IP-CIDR,{rule_value}')
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
    """从本地manual/reject-rules.txt读取规则，并为纯域名自动添加前缀。"""
    manual_rules = set()
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(('#', '!', ';')):
                    if ',' not in line:
                        manual_rules.add(f'DOMAIN-SUFFIX,{line}')
                    else:
                        manual_rules.add(line)
    return manual_rules

def fetch_raw_local_rules(filepath):
    """从本地文件逐行读取原始规则，不做任何格式修改。"""
    raw_rules = set()
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(('#', '!', ';')):
                    raw_rules.add(line)
    else:
        print(f"ℹ️  Info: Raw local rule file not found at {filepath}, skipping.")
    return raw_rules

def fetch_manual_allow_rules(filepath):
    """从本地manual/allow-rules.txt读取白名单域名，返回域名列表。"""
    allow_rules = set()
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(('#', '!', ';', '---')):
                    allow_rules.add(line)
    return allow_rules

# --- 主逻辑 ---

if __name__ == "__main__":
    print("--- Starting Separate Rule Aggregation ---")

    print("\nFetching common manual rules...")
    manual_reject_path = os.path.join("manual", "reject-rules.txt")
    common_manual_reject_rules = fetch_manual_reject_rules(manual_reject_path)
    
    manual_allow_path = os.path.join("manual", "allow-rules.txt")
    common_allow_rules = fetch_manual_allow_rules(manual_allow_path)

    print("\n--- Generating Rules for Loon ---")
    loon_web_rules = fetch_raw_rules(LOON_AD_RULES_URLS)
    loon_combined_rules = loon_web_rules | common_manual_reject_rules
    loon_final_rules = loon_combined_rules - common_allow_rules
    print(f"Found {len(loon_final_rules)} unique rules for Loon.")
    loon_formatted_rules = format_for_loon(loon_final_rules)
    write_rules_to_file(
        os.path.join(LOON_OUTPUT_DIR, "ad-rules.list"), 
        loon_formatted_rules, 
        "Loon Ad Rules (Aggregated)"
    )

    print("\n--- Generating Rules for QuantumultX ---")
    qx_web_rules = fetch_raw_rules(QUANTUMULTX_AD_RULES_URLS)
    
    print("Fetching QX-specific 'raw' manual reject rules...")
    manual_back_rules_path = os.path.join("manual", "reject-rules-back.txt")
    qx_specific_manual_rules = fetch_raw_local_rules(manual_back_rules_path)
    
    qx_combined_rules = qx_web_rules | common_manual_reject_rules | qx_specific_manual_rules
    
    qx_final_rules = qx_combined_rules - common_allow_rules
    
    print(f"Found {len(qx_final_rules)} unique rules for QuantumultX.")
    qx_formatted_rules = format_for_quantumultx(qx_final_rules)
    write_rules_to_file(
        os.path.join(QUANTUMULTX_OUTPUT_DIR, "ad-rules.list"),
        qx_formatted_rules,
        "QuantumultX Ad Rules (Aggregated)"
    )
    
    print("\n--- Separate Rule Aggregation Finished ---")
