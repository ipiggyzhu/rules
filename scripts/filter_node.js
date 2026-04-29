// ============================================================
// Quantumult X 节点过滤脚本 (filter_node.js)
// 过滤订阅中的信息条目, 只保留有效代理节点
// ============================================================

// 1. 黑名单正则: 拥有最高否决权。命中即丢弃, 白名单无法覆盖。
//    维护时直接在 | 后追加关键词即可。
const blacklistRe = /套餐|到期|流量|剩余|重置|官网|过滤|订阅|频道|群组|公告|禁止|说明|推荐|机场|客服|链接|过期|已用|点击|网址|教程|有效期|使用情况|账户|余额|追云国内|追云国外|长期有效|Error|错误|失败|维护|更新中|通知|提示/i;

// 2. 白名单正则: 保护特征明显的合法节点。
//    注意: 两字母英文缩写用 \b 词边界防止误匹配 (如 IN 不会匹配 streamING)
const whitelistRe = new RegExp([
  // 地区 - 中文
  '香港|澳门|台湾|新加坡|日本|韩国|美国|英国|德国|法国|俄罗斯|印度|土耳其|越南|马来西亚|加拿大|澳洲|巴西|阿根廷',
  '荷兰|瑞士|意大利|西班牙|泰国|菲律宾|印尼|墨西哥|智利|南非|埃及|以色列|迪拜|波兰|瑞典|挪威|丹麦|芬兰|爱尔兰|葡萄牙|希腊',
  // 城市 - 中文
  '东京|首尔|莫斯科|伦敦|纽约|洛杉矶|巴黎|柏林|阿姆斯特丹|悉尼|多伦多|温哥华|曼谷|吉隆坡|雅加达|孟买',
  // 地区 - 英文缩写 (词边界保护)
  '\\bHK\\b|\\bMO\\b|\\bTW\\b|\\bSG\\b|\\bJP\\b|\\bKR\\b|\\bUS\\b|\\bUK\\b|\\bDE\\b|\\bFR\\b|\\bRU\\b|\\bIN\\b|\\bTR\\b|\\bVN\\b|\\bMY\\b|\\bCA\\b|\\bAU\\b|\\bNL\\b|\\bCH\\b|\\bIT\\b|\\bES\\b|\\bTH\\b|\\bPH\\b|\\bID\\b|\\bMX\\b|\\bCL\\b|\\bZA\\b|\\bEG\\b|\\bIL\\b|\\bAE\\b',
  // 线路特征
  '专线|IPLC|IEPL|BGP|CN2|GIA|游戏|Game|流媒体|Streaming|解锁|中转|Relay|Premium|Pro|VIP|高速|优化|直连|快速|稳定'
].join('|'), 'i');

// 3. 信息条目模式正则: 匹配各种非节点的信息格式
const infoPatternRe = /^[\u4e00-\u9fa5]{2,8}[:：]\s*[\u4e00-\u9fa5\d\.\s]+(GB|MB|TB|KB|天|小时|年|月|日)?$/i;

// --- 核心逻辑区 ---

const name = $server.name.trim();

// 第一步: 黑名单检查 (最高否决权 - 命中即丢弃, 不可被白名单覆盖)
if (blacklistRe.test(name)) {
  return false;
}

// 第二步: 白名单检查 (保护合法节点)
if (whitelistRe.test(name)) {
  return true;
}

// 第三步: 模式匹配检查 (过滤明显的信息条目)

// 3a. 含冒号的键值对信息 (如: "剩余: 867.6 GB", "状态: 正常")
if (/[:：]/.test(name) && infoPatternRe.test(name)) {
  return false;
}

// 3b. 纯数字+单位 (如: "867.6 GB")
if (/^[\d\.\s]+(GB|MB|TB|KB)$/i.test(name)) {
  return false;
}

// 3c. URL / 链接 (如: "t.me/xxx", "官网 example.com")
if (/(?:https?:\/\/|t\.me\/|\.com|\.cn|\.xyz|\.top)/i.test(name)) {
  return false;
}

// 3d. 纯 emoji / 特殊符号条目 (无实际文字内容)
if (/^[\s\p{Emoji}\p{So}\p{Pd}|•·→←↑↓★☆※]+$/u.test(name)) {
  return false;
}

// 第四步: 启发式分析 (对不黑不白的"中性"条目进行最终裁定)
let features = 0;
if (/\d/.test(name)) features++;           // 特征1: 含数字 (节点通常带编号)
if (/[a-zA-Z]/.test(name)) features++;     // 特征2: 含英文字母
if (name.length > 2 && name.length < 40) features++; // 特征3: 长度合理

// 最终决策: 中性条目需满足 >=2 个特征才保留
return features >= 2;
