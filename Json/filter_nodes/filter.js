// --- 规则配置区 ---

// 1. 黑名单：包含这些词的条目，100%是垃圾信息，立即排除。
const blacklistKeywords = [
  '套餐', '到期', '流量', '剩余', '重置', '时间', '官网', '过滤',
  '订阅', '频道', '群组', '公告', '禁止', '说明', '推荐', '机场',
  '客服', '链接', '过期', '已用', '点击', '网址', '教程',
  '追云国内', '追云国外', 'do not', 'Do not'
];

// 2. 白名单：包含这些词的条目，大概率是有效节点，优先保留。
const whitelistKeywords = [
  // 常见地区
  '香港', '澳门', '台湾', '新加坡', '日本', '韩国', '美国', '英国', '德国', '法国', '俄罗斯', '印度', '土耳其', '越南', '马来西亚', '加拿大', '澳洲', '巴西', '阿根廷',
  // 地区缩写 (不区分大小写)
  'HK', 'MO', 'TW', 'SG', 'JP', 'KR', 'US', 'UK', 'DE', 'FR', 'RU', 'IN', 'TR', 'VN', 'MY', 'CA', 'AU',
  // 技术术语
  '专线', 'IPLC', 'IEPL', 'BGP', 'CN2', 'GIA', '游戏', 'Game', '流媒体', 'Streaming', '解锁', '中转', 'Relay', 'Premium', 'Pro', 'VIP'
];

// --- 主函数 (无需修改) ---
function main(proxies) {
  
  const filteredProxies = proxies.filter(proxy => {
    const name = proxy.name;
    const upperName = name.toUpperCase(); // 创建一个大写版本用于不区分大小写的匹配

    // 第一步：黑名单检查，如果命中，立即排除
    if (blacklistKeywords.some(keyword => name.includes(keyword))) {
      return false;
    }

    // 第二步：白名单检查，如果命中，立即保留
    if (whitelistKeywords.some(keyword => upperName.includes(keyword.toUpperCase()))) {
      return true;
    }

    // 第三步：对未被前两步处理的“中性”条目进行启发式分析
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
    if (name.length > 2 && name.length < 35) {
      features++;
    }
    
    // 决策：对于中性条目，至少需要满足2个或以上特征才被认为是节点
    return features >= 2;
  });
  
  return filteredProxies;
}
