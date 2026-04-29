// ============================================================
// Clash Verge Rev 覆写脚本
// 功能: DNS配置 + 规则集 + 代理组 + 节点信息过滤 + 落地节点链式代理
// ============================================================

// 国内DNS服务器
const domesticNameservers = [
  "https://223.5.5.5/dns-query", // 阿里DoH
  "https://doh.pub/dns-query" // 腾讯DoH
];
// 国外DNS服务器
const foreignNameservers = [
  "https://cloudflare-dns.com/dns-query", // CloudflareDNS
  "https://77.88.8.8/dns-query", // YandexDNS
  "https://8.8.4.4/dns-query#ecs=1.1.1.1/24&ecs-override=true", // GoogleDNS
  "https://208.67.222.222/dns-query#ecs=1.1.1.1/24&ecs-override=true", // OpenDNS
  "https://9.9.9.9/dns-query", // Quad9DNS
];
// DNS配置
const dnsConfig = {
  "enable": true,
  "listen": "0.0.0.0:1053",
  "prefer-h3": false,
  "respect-rules": true,
  "use-system-hosts": false,
  "cache-algorithm": "arc",
  "enhanced-mode": "fake-ip",
  "fake-ip-range": "198.18.0.1/16",
  "fake-ip-filter": [
    // 本地主机/设备
    "+.lan",
    "+.local",
    // Windows网络出现小地球图标
    "+.msftconnecttest.com",
    "+.msftncsi.com",
    // QQ快速登录检测失败
    "localhost.ptlogin2.qq.com",
    "localhost.sec.qq.com",
    // 微信快速登录检测失败
    "localhost.work.weixin.qq.com",
    // 第三方CC公益站
    "+.agentrouter.org",
    "+.code-relay.com",
    "+.gptkey.eu.org",
    "+.cifang.xyz"
  ],
  "default-nameserver": ["223.5.5.5", "1.2.4.8"],
  "nameserver": [...foreignNameservers],
  "proxy-server-nameserver": [...domesticNameservers],
  "direct-nameserver": [...domesticNameservers],
  "direct-nameserver-follow-policy": false,
  "nameserver-policy": {
    "geosite:cn": domesticNameservers
  }
};

// ============================================================
// 节点信息过滤配置
// 用于过滤机场订阅中的非节点信息条目 (到期提醒、流量统计、公告等)
// ============================================================

// 黑名单正则 (命中即丢弃, 最高否决权)
const infoFilterRegex = '套餐|到期|流量|剩余|重置|官网|过滤|订阅|频道|群组|公告|禁止|说明|推荐|机场|客服|链接|过期|已用|点击|网址|教程|有效期|使用情况|账户|余额|长期有效|[Ee]rror|错误|失败|维护|更新中|通知|提示|[Ee]xpire|[Tt]raffic|[Rr]eset';
const infoFilterRe = new RegExp(infoFilterRegex);

// 额外模式检测: 纯数字+单位、URL、纯符号
function isInfoEntry(name) {
  if (!name || typeof name !== 'string') return true;
  const n = name.trim();
  if (n.length === 0) return true;
  // 黑名单关键词
  if (infoFilterRe.test(n)) return true;
  // 纯数字+单位 (如 "867.6 GB")
  if (/^[\d.\s]+(GB|MB|TB|KB)$/i.test(n)) return true;
  // URL / 链接
  if (/(?:https?:\/\/|t\.me\/|\.com[/\s]|\.cn[/\s]|\.xyz[/\s]|\.top[/\s])/i.test(n)) return true;
  // 中文键值对信息 (如 "剩余: 867.6 GB", "状态: 正常")
  if (/^[\u4e00-\u9fa5]{2,8}[:：]\s*.{1,20}$/.test(n) && n.length < 20) return true;
  return false;
}

// ============================================================
// 规则集配置
// ============================================================

// 规则集通用配置
const ruleProviderCommon = {
  "type": "http",
  "format": "yaml",
  "interval": 86400
};
// 规则集配置
const ruleProviders = {
  "reject": {
    ...ruleProviderCommon,
    "behavior": "domain",
    "url": "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/reject.txt",
    "path": "./ruleset/loyalsoldier/reject.yaml"
  },
  "icloud": {
    ...ruleProviderCommon,
    "behavior": "domain",
    "url": "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/icloud.txt",
    "path": "./ruleset/loyalsoldier/icloud.yaml"
  },
  "apple": {
    ...ruleProviderCommon,
    "behavior": "domain",
    "url": "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/apple.txt",
    "path": "./ruleset/loyalsoldier/apple.yaml"
  },
  "google": {
    ...ruleProviderCommon,
    "behavior": "domain",
    "url": "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/google.txt",
    "path": "./ruleset/loyalsoldier/google.yaml"
  },
  "proxy": {
    ...ruleProviderCommon,
    "behavior": "domain",
    "url": "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/proxy.txt",
    "path": "./ruleset/loyalsoldier/proxy.yaml"
  },
  "direct": {
    ...ruleProviderCommon,
    "behavior": "domain",
    "url": "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/direct.txt",
    "path": "./ruleset/loyalsoldier/direct.yaml"
  },
  "private": {
    ...ruleProviderCommon,
    "behavior": "domain",
    "url": "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/private.txt",
    "path": "./ruleset/loyalsoldier/private.yaml"
  },
  "gfw": {
    ...ruleProviderCommon,
    "behavior": "domain",
    "url": "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/gfw.txt",
    "path": "./ruleset/loyalsoldier/gfw.yaml"
  },
  "tld-not-cn": {
    ...ruleProviderCommon,
    "behavior": "domain",
    "url": "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/tld-not-cn.txt",
    "path": "./ruleset/loyalsoldier/tld-not-cn.yaml"
  },
  "telegramcidr": {
    ...ruleProviderCommon,
    "behavior": "ipcidr",
    "url": "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/telegramcidr.txt",
    "path": "./ruleset/loyalsoldier/telegramcidr.yaml"
  },
  "cncidr": {
    ...ruleProviderCommon,
    "behavior": "ipcidr",
    "url": "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/cncidr.txt",
    "path": "./ruleset/loyalsoldier/cncidr.yaml"
  },
  "lancidr": {
    ...ruleProviderCommon,
    "behavior": "ipcidr",
    "url": "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/lancidr.txt",
    "path": "./ruleset/loyalsoldier/lancidr.yaml"
  },
  "applications": {
    ...ruleProviderCommon,
    "behavior": "classical",
    "url": "https://testingcf.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/applications.txt",
    "path": "./ruleset/loyalsoldier/applications.yaml"
  },
  "openai": {
    ...ruleProviderCommon,
    "behavior": "classical",
    "url": "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/classical/openai.yaml",
    "path": "./ruleset/MetaCubeX/openai.yaml"
  },
  "anthropic": {
    ...ruleProviderCommon,
    "behavior": "classical",
    "url": "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/classical/anthropic.yaml",
    "path": "./ruleset/MetaCubeX/anthropic.yaml"
  },
  "google-gemini": {
    ...ruleProviderCommon,
    "behavior": "classical",
    "url": "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/classical/google-gemini.yaml",
    "path": "./ruleset/MetaCubeX/google-gemini.yaml"
  },
  "xai": {
    ...ruleProviderCommon,
    "behavior": "classical",
    "url": "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/classical/xai.yaml",
    "path": "./ruleset/MetaCubeX/xai.yaml"
  },
  "microsoft": {
    ...ruleProviderCommon,
    "behavior": "classical",
    "url": "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/classical/microsoft.yaml",
    "path": "./ruleset/MetaCubeX/microsoft.yaml"
  },
};

// 规则
const rules = [
  // 额外自定义规则
  "PROCESS-NAME,steam.exe,🐬 自定义直连",
  "DOMAIN-SUFFIX,linux.do,🐳 自定义代理",
  "DOMAIN-SUFFIX,immersivetranslate.com,🐳 自定义代理",
  // 自定义规则
  "DOMAIN-SUFFIX,googleapis.cn,🔰 模式选择", // Google服务
  "DOMAIN-SUFFIX,gstatic.com,🔰 模式选择", // Google静态资源
  "DOMAIN-SUFFIX,github.io,🔰 模式选择", // Github Pages
  "DOMAIN,v2rayse.com,🔰 模式选择", // V2rayse节点工具
  // MetaCubeX 规则集
  "RULE-SET,openai,💸 ChatGPT-Gemini-XAI-Perplexity",
  "RULE-SET,anthropic,💵 Claude",
  "RULE-SET,google-gemini,💸 ChatGPT-Gemini-XAI-Perplexity",
  "RULE-SET,xai,💸 ChatGPT-Gemini-XAI-Perplexity",
  // Loyalsoldier 规则集
  "RULE-SET,applications,🔗 全局直连",
  "RULE-SET,private,🔗 全局直连",
  "RULE-SET,reject,🥰 广告过滤",
  "RULE-SET,microsoft,Ⓜ️ 微软服务",
  "RULE-SET,google,📢 谷歌服务",
  "RULE-SET,proxy,🔰 模式选择",
  "RULE-SET,gfw,🔰 模式选择",
  "RULE-SET,tld-not-cn,🔰 模式选择",
  "RULE-SET,direct,🔗 全局直连",
  "RULE-SET,lancidr,🔗 全局直连,no-resolve",
  "RULE-SET,cncidr,🔗 全局直连,no-resolve",
  // 其他规则
  "GEOIP,LAN,🔗 全局直连,no-resolve",
  "GEOIP,CN,🔗 全局直连,no-resolve",
  "MATCH,🐟 漏网之鱼"
];

// 代理组通用配置
const groupBaseOption = {
  "interval": 0,
  "timeout": 3000,
  "url": "https://www.google.com/generate_204",
  "lazy": true,
  "max-failed-times": 3,
  "hidden": false
};

// ============================================================
// 🔴 落地节点配置区
// ============================================================
const landingNodeProxies = [
  // 示例配置 (使用前请填写 server/username/password)
  {
    "name": "us1",
    "server": "", // 替换成落地节点IP
    "port": 443,       // 替换端口
    "type": "socks5",
    "username": "",  // 替换用户名
    "password": "",  // 替换密码
    "tls": false,
    "skip-cert-verify": true,
    "udp": true,
    "dialer-proxy": "⚙️ 节点选择" // 链式代理的前置节点组
  }
  // 如果有更多落地节点，复制上面的块并继续添加
];

// 代理组配置
const proxyGroupsConfig = [
  {
    ...groupBaseOption,
    "name": "🔰 模式选择",
    "type": "select",
    "proxies": [
      "⚙️ 节点选择",
      "🕊️ 落地节点",
      "🔗 全局直连"
    ]
  },
  {
    ...groupBaseOption,
    "name": "⚙️ 节点选择",
    "type": "select",
    "proxies": ["♻️ 延迟选优", "🚑 故障转移", "⚖️ 负载均衡(散列)", "☁️ 负载均衡(轮询)"],
    "include-all": true,
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/adjust.svg"
  },
  {
    ...groupBaseOption,
    "name": "🕊️ 落地节点",
    "type": "select",
    "proxies": [],
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/openwrt.svg"
  },
  {
    ...groupBaseOption,
    "name": "♻️ 延迟选优",
    "type": "url-test",
    "tolerance": 50,
    "include-all": true,
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/speed.svg"
  },
  {
    ...groupBaseOption,
    "name": "🚑 故障转移",
    "type": "fallback",
    "include-all": true,
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/ambulance.svg"
  },
  {
    ...groupBaseOption,
    "name": "⚖️ 负载均衡(散列)",
    "type": "load-balance",
    "strategy": "consistent-hashing",
    "include-all": true,
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/merry_go.svg"
  },
  {
    ...groupBaseOption,
    "name": "☁️ 负载均衡(轮询)",
    "type": "load-balance",
    "strategy": "round-robin",
    "include-all": true,
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/balance.svg"
  },
  {
    ...groupBaseOption,
    "name": "🌍 国外媒体",
    "type": "select",
    "proxies": ["🔰 模式选择", "⚙️ 节点选择", "🕊️ 落地节点", "♻️ 延迟选优", "🚑 故障转移", "⚖️ 负载均衡(散列)", "☁️ 负载均衡(轮询)", "🔗 全局直连"],
    "include-all": true,
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/youtube.svg"
  },
  {
    ...groupBaseOption,
    "name": "💸 ChatGPT-Gemini-XAI-Perplexity",
    "type": "select",
    "proxies": ["🔰 模式选择", "⚙️ 节点选择", "🕊️ 落地节点", "🔗 全局直连", "♻️ 延迟选优", "🚑 故障转移", "⚖️ 负载均衡(散列)", "☁️ 负载均衡(轮询)"],
    "include-all": true,
    "exclude-filter": "(?i)港|hk|hongkong|hong kong|俄|ru|russia|澳|macao",
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/chatgpt.svg"
  },
  {
    ...groupBaseOption,
    "name": "💵 Claude",
    "type": "select",
    "proxies": ["🔰 模式选择", "⚙️ 节点选择", "🕊️ 落地节点", "🔗 全局直连", "♻️ 延迟选优", "🚑 故障转移", "⚖️ 负载均衡(散列)", "☁️ 负载均衡(轮询)"],
    "include-all": true,
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/claude.svg"
  },
  {
    ...groupBaseOption,
    "name": "📢 谷歌服务",
    "type": "select",
    "proxies": ["🔰 模式选择", "⚙️ 节点选择", "🕊️ 落地节点", "♻️ 延迟选优", "🚑 故障转移", "⚖️ 负载均衡(散列)", "☁️ 负载均衡(轮询)", "🔗 全局直连"],
    "include-all": true,
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/google.svg"
  },
  {
    ...groupBaseOption,
    "name": "Ⓜ️ 微软服务",
    "type": "select",
    "proxies": ["🔰 模式选择", "⚙️ 节点选择", "🕊️ 落地节点", "🔗 全局直连", "♻️ 延迟选优", "🚑 故障转移", "⚖️ 负载均衡(散列)", "☁️ 负载均衡(轮询)"],
    "include-all": true,
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/microsoft.svg"
  },
  {
    ...groupBaseOption,
    "name": "🥰 广告过滤",
    "type": "select",
    "proxies": ["REJECT", "DIRECT"],
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/bug.svg"
  },
  {
    ...groupBaseOption,
    "name": "🔗 全局直连",
    "type": "select",
    "proxies": ["DIRECT", "⚙️ 节点选择", "♻️ 延迟选优", "🚑 故障转移", "⚖️ 负载均衡(散列)", "☁️ 负载均衡(轮询)"],
    "include-all": true,
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/link.svg"
  },
  {
    ...groupBaseOption,
    "name": "❌ 全局拦截",
    "type": "select",
    "proxies": ["REJECT", "DIRECT"],
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/block.svg"
  },
  {
    ...groupBaseOption,
    "name": "🐬 自定义直连",
    "type": "select",
    "include-all": true,
    "proxies": ["🔗 全局直连", "🔰 模式选择", "⚙️ 节点选择", "♻️ 延迟选优", "🚑 故障转移", "⚖️ 负载均衡(散列)", "☁️ 负载均衡(轮询)"],
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/unknown.svg"
  },
  {
    ...groupBaseOption,
    "name": "🐳 自定义代理",
    "type": "select",
    "include-all": true,
    "proxies": ["🔰 模式选择", "⚙️ 节点选择", "🕊️ 落地节点", "♻️ 延迟选优", "🚑 故障转移", "⚖️ 负载均衡(散列)", "☁️ 负载均衡(轮询)", "🔗 全局直连"],
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/openwrt.svg"
  },
  {
    ...groupBaseOption,
    "name": "🐟 漏网之鱼",
    "type": "select",
    "proxies": ["🔰 模式选择", "⚙️ 节点选择", "🕊️ 落地节点", "♻️ 延迟选优", "🚑 故障转移", "⚖️ 负载均衡(散列)", "☁️ 负载均衡(轮询)", "🔗 全局直连"],
    "include-all": true,
    "icon": "https://testingcf.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/fish.svg"
  }
];

// ============================================================
// 多订阅合并
// ============================================================
const proxyProviders = {
  // 在这里添加你的机场订阅
  "zhuiyun": {
    "type": "http",
    "url": "https://midxswez.haawx.com/api/v1/clienFPBngt80pFn1?token=9446cdd625edff748cbf1c2693ade86f",
    "interval": 86400,
    "proxy": "🔰 模式选择",
    "health-check": {
      "enable": true,
      "url": "https://www.google.com/generate_204",
      "interval": 300
    }
  },
  "llgic": {
    "type": "http",
    "url": "https://drfytjmjhggnrgergergergerg6c.xyz/api/v1/client/subscribe?token=f055cc2456ff2dfde93e743f214d9335",
    "interval": 86400,
    "proxy": "🔰 模式选择",
    "health-check": {
      "enable": true,
      "url": "https://www.google.com/generate_204",
      "interval": 300
    }
  }
};

// ============================================================
// 程序入口
// ============================================================
function main(config) {
  const originalProxies = config?.proxies ? [...config.proxies] : [];
  const originalProviders = config?.["proxy-providers"] || {};

  // --- 注入基础配置 ---
  config["dns"] = dnsConfig;
  config["rule-providers"] = ruleProviders;
  config["rules"] = rules;

  // --- 过滤信息条目 + 处理原始代理 ---
  const filteredProxies = originalProxies.filter(proxy => {
    if (!proxy || typeof proxy !== 'object' || !proxy.name) return false;
    // 过滤信息条目 (到期提醒、流量统计、公告等)
    if (isInfoEntry(proxy.name)) return false;
    // 保留并启用 UDP
    proxy.udp = true;
    return true;
  });

  // --- 落地节点处理 (跳过未配置的空节点) ---
  const validLandingNodes = landingNodeProxies.filter(p => p.server && p.server.length > 0);
  const landingNames = validLandingNodes.map(p => p.name);

  // 合并代理列表
  config["proxies"] = [...filteredProxies, ...validLandingNodes];

  // --- 为所有 proxy-provider 注入 exclude-filter (过滤信息条目) ---
  const allProviders = { ...originalProviders, ...proxyProviders };
  for (const key of Object.keys(allProviders)) {
    const existing = allProviders[key]["exclude-filter"];
    allProviders[key]["exclude-filter"] = existing
      ? `${existing}|${infoFilterRegex}`
      : infoFilterRegex;
  }
  config["proxy-providers"] = allProviders;

  // --- 正则转义函数 ---
  function escapeForRegExp(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // --- 落地节点排除逻辑 (防止循环代理) ---
  const escapedNames = landingNames.map(escapeForRegExp).join('|');
  const excludeLandingFilter = escapedNames ? `^(?:${escapedNames})$` : null;

  const groupsToExcludeLandingNodes = [
    "⚙️ 节点选择",
    "♻️ 延迟选优",
    "🚑 故障转移",
    "⚖️ 负载均衡(散列)",
    "☁️ 负载均衡(轮询)"
  ];

  // --- 组装代理组 ---
  const finalProxyGroups = proxyGroupsConfig.map(group => {
    // 落地节点组: 动态填充有效的落地节点名
    if (group.name === "🕊️ 落地节点") {
      group.proxies = landingNames.length > 0 ? [...landingNames] : ["DIRECT"];
    }

    // 指定组排除落地节点 (防循环)
    if (groupsToExcludeLandingNodes.includes(group.name) && excludeLandingFilter) {
      const existing = group["exclude-filter"];
      group["exclude-filter"] = existing
        ? `(${existing})|(${excludeLandingFilter})`
        : excludeLandingFilter;
    }
    return group;
  });

  config["proxy-groups"] = finalProxyGroups;
  return config;
}
