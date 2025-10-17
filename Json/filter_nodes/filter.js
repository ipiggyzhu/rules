// --- 规则配置区 ---
const positiveRegions = ['香港', '澳门', '台湾', '新加坡', '日本', '韩国', '美国', '英国', '德国', '法国', '俄罗斯', '印度', '土耳其', '越南', '马来西亚', '加拿大', '澳洲', '巴西', '阿根廷', 'HK', 'MO', 'TW', 'SG', 'JP', 'KR', 'US', 'UK', 'DE', 'FR', 'RU', 'IN', 'TR', 'VN', 'MY', 'CA', 'AU'];
const positiveTech = ['专线', 'IPLC', 'IEPL', 'BGP', 'CN2', 'GIA', '游戏', 'Game', '流媒体', 'Streaming', '解锁', 'Relay', '中转', 'Premium', 'Pro', 'VIP'];
const negativeKeywords = ['套餐', '到期', '流量', '剩余', '重置', '时间', '官网', '过滤', '订阅', '频道', '群组', '公告', '禁止', '说明', '推荐', '机场', '官网', '客服', '链接', '过期', '已用', '官网', '点击', '网址', '教程'];

// --- 核心逻辑区 ---
function getScore(proxyName) {
  let score = 0;
  const name = proxyName.toUpperCase();
  if (proxyName.startsWith('http://') || proxyName.startsWith('https://')) return -99;
  positiveRegions.forEach(k => { if (name.includes(k.toUpperCase())) score += 2; });
  positiveTech.forEach(k => { if (name.includes(k.toUpperCase())) score += 1; });
  if (/\d/.test(name)) score += 1;
  negativeKeywords.forEach(k => { if (name.includes(k.toUpperCase())) score -= 3; });
  if (proxyName.length <= 2 || proxyName.length > 40) score -= 2;
  return score;
}

// --- 主函数 ---
function main(proxies) {
  const filteredProxies = proxies.filter(proxy => {
    const score = getScore(proxy.name);
    return score > 0;
  });
  return filteredProxies;
}
