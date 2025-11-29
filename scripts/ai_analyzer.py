"""
AI 域名分析器

功能：使用 AI 分析域名是否为广告/追踪域名
支持：任何 OpenAI 兼容的 API（包括第三方公益站）

环境变量：
- AI_API_URL: AI API 地址（如 https://api.openai.com/v1）
- AI_API_KEY: API 密钥
- AI_MODEL: 模型名称（默认 gpt-3.5-turbo）
- WORKER_URL: Cloudflare Worker 地址
- WORKER_TOKEN: Worker 认证 Token
"""

import os
import json
import requests
import time
from typing import List, Dict, Tuple

# 配置
AI_API_URL = os.environ.get('AI_API_URL', 'https://api.openai.com/v1')
AI_API_KEY = os.environ.get('AI_API_KEY', '')
AI_MODEL = os.environ.get('AI_MODEL', 'gpt-3.5-turbo')
WORKER_URL = os.environ.get('WORKER_URL', '')
WORKER_TOKEN = os.environ.get('WORKER_TOKEN', '')

# 路径
SOURCES_DIR = 'sources'
BLACKLIST_FILE = os.path.join(SOURCES_DIR, 'ad-blacklist.txt')
WHITELIST_FILE = os.path.join(SOURCES_DIR, 'ad-whitelist.txt')

# 已知广告关键词（预过滤）
AD_KEYWORDS = [
    'ad', 'ads', 'adv', 'advert', 'advertising',
    'track', 'tracker', 'tracking',
    'analytics', 'analytic', 'stats', 'stat', 'statistics',
    'telemetry', 'metric', 'metrics',
    'pixel', 'beacon', 'log', 'logging',
    'click', 'clicks', 'clk',
    'pcdn', 'cdn-ad', 'adcdn',
    'dsp', 'ssp', 'rtb',
    'taboola', 'outbrain', 'criteo', 'doubleclick'
]

# 已知安全域名（跳过分析）
SAFE_PATTERNS = [
    'apple.com', 'microsoft.com', 'google.com', 'github.com',
    'cloudflare.com', 'amazonaws.com', 'azure.com',
    'qq.com', 'weixin.qq.com', 'alipay.com', 'taobao.com',
    'baidu.com', 'bilibili.com', 'zhihu.com', 'douyin.com'
]


def load_existing_rules() -> Tuple[set, set]:
    """加载现有的黑名单和白名单"""
    blacklist = set()
    whitelist = set()

    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    blacklist.add(line)

    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    whitelist.add(line)

    return blacklist, whitelist


def fetch_pending_domains() -> List[str]:
    """从 Worker 获取待分析的域名"""
    if not WORKER_URL or not WORKER_TOKEN:
        print("错误：未配置 WORKER_URL 或 WORKER_TOKEN")
        return []

    try:
        response = requests.get(
            f"{WORKER_URL}/domains",
            headers={'Authorization': f'Bearer {WORKER_TOKEN}'},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get('domains', [])
    except Exception as e:
        print(f"获取域名失败: {e}")
        return []


def clear_pending_domains():
    """清空 Worker 中的待处理域名"""
    try:
        requests.post(
            f"{WORKER_URL}/clear",
            headers={'Authorization': f'Bearer {WORKER_TOKEN}'},
            timeout=30
        )
    except Exception as e:
        print(f"清空域名失败: {e}")


def is_likely_ad(domain: str) -> bool:
    """预过滤：基于关键词判断是否可能是广告域名"""
    domain_lower = domain.lower()
    for keyword in AD_KEYWORDS:
        if keyword in domain_lower:
            return True
    return False


def is_safe_domain(domain: str) -> bool:
    """判断是否为已知安全域名"""
    domain_lower = domain.lower()
    for safe in SAFE_PATTERNS:
        if domain_lower.endswith(safe) or domain_lower == safe:
            return True
    return False


def analyze_with_ai(domains: List[str]) -> Dict[str, bool]:
    """
    使用 AI 分析域名列表
    返回：{域名: 是否为广告}
    """
    if not domains:
        return {}

    if not AI_API_KEY:
        print("警告：未配置 AI_API_KEY，跳过 AI 分析")
        return {}

    prompt = f"""你是一个网络安全专家，专门分析域名是否为广告、追踪、遥测或其他不需要的域名。

请分析以下域名列表，判断每个域名是否应该被屏蔽。

判断标准：
1. 广告域名（ad, ads, advertising 等）→ 屏蔽
2. 追踪域名（track, tracker, analytics 等）→ 屏蔽
3. 遥测域名（telemetry, metrics, beacon 等）→ 屏蔽
4. 数据收集域名（log, stats, pixel 等）→ 屏蔽
5. 正常服务域名（CDN、API、网站主域名等）→ 不屏蔽
6. 不确定的域名 → 不屏蔽（宁可漏过，不可误杀）

域名列表：
{json.dumps(domains, indent=2)}

请以 JSON 格式回复，格式为：
{{"domain1": true, "domain2": false, ...}}

其中 true 表示应该屏蔽，false 表示不应该屏蔽。
只回复 JSON，不要其他内容。"""

    try:
        response = requests.post(
            f"{AI_API_URL}/chat/completions",
            headers={
                'Authorization': f'Bearer {AI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': AI_MODEL,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.1,
                'max_tokens': 2000
            },
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        content = result['choices'][0]['message']['content'].strip()

        # 提取 JSON
        if '```' in content:
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]

        return json.loads(content)

    except json.JSONDecodeError as e:
        print(f"AI 响应解析失败: {e}")
        print(f"原始响应: {content if 'content' in dir() else 'N/A'}")
        return {}
    except Exception as e:
        print(f"AI 分析失败: {e}")
        return {}


def save_blacklist(domains: set):
    """保存黑名单"""
    os.makedirs(SOURCES_DIR, exist_ok=True)

    # 读取现有内容（保留注释）
    existing_lines = []
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            existing_lines = [line.strip() for line in f if line.strip().startswith('#')]

    with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
        # 写入注释
        for line in existing_lines:
            f.write(f"{line}\n")
        if existing_lines:
            f.write("\n")

        # 写入域名（排序）
        for domain in sorted(domains):
            f.write(f"{domain}\n")


def main():
    print("=" * 60)
    print("AI 域名分析器")
    print("=" * 60)

    # 加载现有规则
    blacklist, whitelist = load_existing_rules()
    print(f"\n当前黑名单: {len(blacklist)} 条")
    print(f"当前白名单: {len(whitelist)} 条")

    # 获取待分析域名
    print("\n获取待分析域名...")
    pending = fetch_pending_domains()
    print(f"待分析: {len(pending)} 个域名")

    if not pending:
        print("没有待分析的域名")
        return

    # 过滤已存在的域名
    new_domains = []
    for domain in pending:
        if domain in blacklist or domain in whitelist:
            continue
        if is_safe_domain(domain):
            continue
        new_domains.append(domain)

    print(f"过滤后: {len(new_domains)} 个新域名")

    if not new_domains:
        print("没有新域名需要分析")
        clear_pending_domains()
        return

    # 预过滤：基于关键词
    likely_ads = []
    need_ai_analysis = []

    for domain in new_domains:
        if is_likely_ad(domain):
            likely_ads.append(domain)
        else:
            need_ai_analysis.append(domain)

    print(f"关键词匹配广告: {len(likely_ads)} 个")
    print(f"需要 AI 分析: {len(need_ai_analysis)} 个")

    # AI 分析（分批处理，每批 20 个）
    ai_results = {}
    batch_size = 20

    for i in range(0, len(need_ai_analysis), batch_size):
        batch = need_ai_analysis[i:i + batch_size]
        print(f"\nAI 分析批次 {i // batch_size + 1}: {len(batch)} 个域名")

        results = analyze_with_ai(batch)
        ai_results.update(results)

        # 避免请求过快
        if i + batch_size < len(need_ai_analysis):
            time.sleep(2)

    # 汇总结果
    new_ads = set(likely_ads)
    for domain, is_ad in ai_results.items():
        if is_ad:
            new_ads.add(domain)

    print(f"\n新发现广告域名: {len(new_ads)} 个")

    if new_ads:
        # 更新黑名单
        updated_blacklist = blacklist | new_ads
        save_blacklist(updated_blacklist)
        print(f"已更新黑名单，总计: {len(updated_blacklist)} 条")

        # 显示新增的域名
        print("\n新增域名:")
        for domain in sorted(new_ads)[:20]:
            print(f"  + {domain}")
        if len(new_ads) > 20:
            print(f"  ... 等共 {len(new_ads)} 个")

    # 清空待处理
    clear_pending_domains()
    print("\n已清空待处理队列")

    print("\n" + "=" * 60)
    print("分析完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
