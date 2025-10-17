// --- 规则配置区 ---

// 1. 黑名单：拥有最高否决权。包含这些词的条目，100%是垃圾信息，立即排除。
const blacklistKeywords = [
  '套餐', '到期', '流量', '剩余', '重置', '时间', '官网', '过滤',
  '订阅', '频道', '群组', '公告', '禁止', '说明', '推荐', '机场',
  '客服', '链接', '过期', '已用', '点击', '网址', '教程',
  '追云国内', '追云国外', 'do not', 'Do not'
];

// 2. 白名单：用于优先保留特征明显的节点。
const whitelistKeywords = [
  '香港', '澳门', '台湾', '新加坡', '日本', '韩国', '美国', '英国', '德国', '法国', '俄罗斯', '印度', '土耳其', '越南', '马来西亚', '加拿大', '澳洲', '巴西', '阿根廷',
  'HK', 'MO', 'TW', 'SG', 'JP', 'KR', 'US', 'UK', 'DE', 'FR', 'RU', 'IN', 'TR', 'VN', 'MY', 'CA', 'AU',
  '专线', 'IPLC', 'IEPL', 'BGP', 'CN2', 'GIA', '游戏', 'Game', '流媒体', 'Streaming', '解锁', '中转', 'Relay', 'Premium', 'Pro', 'VIP'
];

// --- 主函数 ---
function main(proxies) {
  
  const filteredProxies = proxies.filter(proxy => {
    const name = proxy.name;
    const upperName = name.toUpperCase();

    // 修正后的第一步：黑名单检查。如果命中，立即返回 false 排除，不再执行任何后续判断。
    if (blacklistKeywords.some(keyword => name.includes(keyword))) {
      return false;
    }

    // 第二步：白名单检查。只有在没有命中黑名单的前提下，才会执行这一步。
    if (whitelistKeywords.some(keyword => upperName.includes(keyword.toUpperCase()))) {
      return true;
    }

    // 第三步：启发式分析。仅对不黑不白的“中性”条目执行。
    let features = 0;
    if (/\d/.test(name)) features++;
    if (/[a-zA-Z]/.test(name)) features++;
    if (name.length > 2 && name.length < 35) features++;
    
    return features >= 2;
  });
  
  return filteredProxies;
}
