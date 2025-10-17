// 1. 正面关键词：包含这些词会加分，是节点的重要标志。
const positiveRegions = ['香港', '澳门', '台湾', '新加坡', '日本', '韩国', '美国', '英国', '德国', '法国', '俄罗斯', '印度', '土耳其', '越南', '马来西亚', '加拿大', '澳洲', '巴西', '阿根廷', 'HK', 'MO', 'TW', 'SG', 'JP', 'KR', 'US', 'UK', 'DE', 'FR', 'RU', 'IN', 'TR', 'VN', 'MY', 'CA', 'AU'];
const positiveTech = ['专线', 'IPLC', 'IEPL', 'BGP', 'CN2', 'GIA', '游戏', 'Game', '流媒体', 'Streaming', '解锁', 'Relay', '中转', 'Premium', 'Pro', 'VIP'];

// 2. 负面关键词：包含这些词会扣分，大概率不是节点。
const negativeKeywords = ['套餐', '到期', '流量', '剩余', '重置', '时间', '官网', '过滤', '订阅', '频道', '群组', '公告', '禁止', '说明', '推荐', '机场', '官网', '客服', '链接', '过期', '已用', '官网', '点击', '网址', '教程'];

// --- 核心逻辑区 ---

function getScore(proxyName) {
  let score = 0;
  const name = proxyName.toUpperCase(); // 转换为大写，方便匹配

  // 规则1: 如果是网址，直接判为垃圾信息 (-99分)
  if (proxyName.startsWith('http://') || proxyName.startsWith('https://')) {
    return -99;
  }

  // 规则2: 包含正面地区关键词，每个加2分
  positiveRegions.forEach(keyword => {
    if (name.includes(keyword.toUpperCase())) {
      score += 2;
    }
  });

  // 规则3: 包含正面技术关键词，每个加1分
  positiveTech.forEach(keyword => {
    if (name.includes(keyword.toUpperCase())) {
      score += 1;
    }
  });

  // 规则4: 包含数字，加1分 (节点名通常带编号)
  if (/\d/.test(name)) {
    score += 1;
  }

  // 规则5: 包含负面关键词，每个扣3分
  negativeKeywords.forEach(keyword => {
    if (name.includes(keyword.toUpperCase())) {
      score -= 3;
    }
  });
  
  // 规则6: 名字太短（小于等于2个字符）或太长（大于40个字符），可能是无效信息，扣分
  if (proxyName.length <= 2 || proxyName.length > 40) {
      score -= 2;
  }

  return score;
}

module.exports.main = (proxies) => {
  console.log(`智能过滤前节点数量: ${proxies.length}`);

  const filteredProxies = proxies.filter(proxy => {
    const score = getScore(proxy.name);
    // 阈值设为大于0，即总分必须是正数才被认为是有效节点
    // 可以根据需要调整这个阈值，比如 score >= 0
    return score > 0;
  });

  console.log(`智能过滤后节点数量: ${filteredProxies.length}`);
  return filteredProxies;
};
