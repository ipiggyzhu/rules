// 1. 黑名单: 拥有最高否决权。包含这些词的条目, 100%会被过滤。
const blacklist = [
  '套餐', '到期', '流量', '剩余', '重置', '时间', '官网', '过滤',
  '订阅', '频道', '群组', '公告', '禁止', '说明', '推荐', '机场',
  '客服', '链接', '过期', '已用', '点击', '网址', '教程',
  '追云国内', '追云国外'
];

// 2. 白名单: 用于优先保留特征明显的节点。
const whitelist = [
  '香港', '澳门', '台湾', '新加坡', '日本', '韩国', '美国', '英国', '德国', '法国', '俄罗斯', '印度', '土耳其', '越南', '马来西亚', '加拿大', '澳洲', '巴西', '阿根廷',
  'HK', 'MO', 'TW', 'SG', 'JP', 'KR', 'US', 'UK', 'DE', 'FR', 'RU', 'IN', 'TR', 'VN', 'MY', 'CA', 'AU',
  '专线', 'IPLC', 'IEPL', 'BGP', 'CN2', 'GIA', '游戏', 'Game', '流媒体', 'Streaming', '解锁', '中转', 'Relay', 'Premium', 'Pro', 'VIP'
];

// --- 核心逻辑区 ---

// 从全局变量 $server 中获取当前节点的名字
const name = $server.name;
const upperName = name.toUpperCase(); // 创建一个大写版本, 用于不区分大小写的匹配

// 第一步: 黑名单检查 (最高优先级)
for (let i = 0; i < blacklist.length; i++) {
  if (name.indexOf(blacklist[i]) !== -1) {
    return false; // 命中黑名单, 立即丢弃
  }
}

// 第二步: 白名单检查 (仅在未命中黑名单时执行)
for (let i = 0; i < whitelist.length; i++) {
  // 对白名单进行不区分大小写的检查
  if (upperName.indexOf(whitelist[i].toUpperCase()) !== -1) {
    return true; // 命中白名单, 立即保留
  }
}

// 第三步: 启发式分析 (对不黑不白的“中性”条目进行最终裁定)
let features = 0;
// 特征1: 包含数字 (节点通常带编号)
if (/\d/.test(name)) {
  features++;
}
// 特征2: 包含英文字母 (很多节点名包含英文)
if (/[a-zA-Z]/.test(name)) {
  features++;
}
// 特征3: 名字长度合理 (太长或太短都可能是无效信息)
if (name.length > 2 && name.length < 40) {
  features++;
}

// 最终决策: 对于中性条目, 至少需要满足2个或以上特征才被认为是有效节点
return features >= 2;
