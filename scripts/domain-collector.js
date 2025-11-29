/**
 * Quantumult X 域名收集脚本
 *
 * 功能：收集访问的域名并定时上报到 Cloudflare Worker
 *
 * 配置方法（添加到 quantumultx.conf）：
 *
 * [rewrite_local]
 * ^https?:\/\/.+ url script-request-header https://raw.githubusercontent.com/ipiggyzhu/rules/main/scripts/domain-collector.js
 *
 * [task_local]
 * 0 */6 * * * https://raw.githubusercontent.com/ipiggyzhu/rules/main/scripts/domain-collector.js, tag=域名上报, enabled=true
 *
 * [mitm]
 * hostname = *
 *
 * 首次使用请在 BoxJS 或手动设置：
 * - domain_collector_url: 你的 Worker 地址
 * - domain_collector_token: 你的 AUTH_TOKEN
 */

const $ = new Env('域名收集器');

// 配置
const WORKER_URL = $.getdata('domain_collector_url') || '';
const AUTH_TOKEN = $.getdata('domain_collector_token') || '';
const STORAGE_KEY = 'collected_domains';
const MAX_DOMAINS = 500; // 本地最多存储数量
const REPORT_THRESHOLD = 50; // 达到多少个触发上报

// 已知的安全域名（不收集）
const SAFE_DOMAINS = new Set([
  'apple.com', 'icloud.com', 'googleapis.com', 'gstatic.com',
  'cloudflare.com', 'github.com', 'githubusercontent.com',
  'qq.com', 'weixin.qq.com', 'wechat.com',
  'alipay.com', 'taobao.com', 'tmall.com', 'alibaba.com',
  'baidu.com', 'bdstatic.com', 'bcebos.com',
  'jd.com', '360buyimg.com',
  'bilibili.com', 'hdslb.com', 'bilivideo.com',
  'douyin.com', 'tiktok.com', 'bytedance.com',
  'weibo.com', 'sinaimg.cn',
  'zhihu.com', 'zhimg.com'
]);

// 判断是否应该收集该域名
function shouldCollect(domain) {
  if (!domain) return false;

  // 跳过 IP 地址
  if (/^\d+\.\d+\.\d+\.\d+$/.test(domain)) return false;

  // 跳过本地域名
  if (domain.endsWith('.local') || domain === 'localhost') return false;

  // 获取主域名
  const parts = domain.split('.');
  if (parts.length < 2) return false;

  const mainDomain = parts.slice(-2).join('.');

  // 跳过安全域名
  if (SAFE_DOMAINS.has(mainDomain)) return false;

  // 跳过已知安全后缀的子域名
  for (const safe of SAFE_DOMAINS) {
    if (domain.endsWith('.' + safe)) return false;
  }

  return true;
}

// 提取主域名（用于去重）
function extractMainDomain(domain) {
  const parts = domain.split('.');
  if (parts.length <= 2) return domain;

  // 处理常见的二级域名后缀
  const secondLevel = ['com', 'net', 'org', 'edu', 'gov', 'co'];
  if (parts.length >= 3 && secondLevel.includes(parts[parts.length - 2])) {
    return parts.slice(-3).join('.');
  }

  return parts.slice(-2).join('.');
}

// 收集域名（请求时触发）
function collectDomain() {
  if (typeof $request === 'undefined') return;

  const url = $request.url;
  if (!url) return;

  try {
    const hostname = new URL(url).hostname;

    if (!shouldCollect(hostname)) return;

    const mainDomain = extractMainDomain(hostname);

    // 获取已收集的域名
    let collected = JSON.parse($.getdata(STORAGE_KEY) || '[]');
    const collectedSet = new Set(collected);

    // 添加新域名
    if (!collectedSet.has(mainDomain)) {
      collected.push(mainDomain);

      // 限制数量
      if (collected.length > MAX_DOMAINS) {
        collected = collected.slice(-MAX_DOMAINS);
      }

      $.setdata(JSON.stringify(collected), STORAGE_KEY);

      // 达到阈值自动上报
      if (collected.length >= REPORT_THRESHOLD && WORKER_URL) {
        reportDomains();
      }
    }
  } catch (e) {
    // 忽略错误
  }
}

// 上报域名到 Worker
async function reportDomains() {
  if (!WORKER_URL || !AUTH_TOKEN) {
    $.msg('域名收集器', '请先配置 Worker URL 和 Token', '');
    return;
  }

  const collected = JSON.parse($.getdata(STORAGE_KEY) || '[]');

  if (collected.length === 0) {
    $.msg('域名收集器', '没有待上报的域名', '');
    return;
  }

  try {
    const response = await $.http.post({
      url: `${WORKER_URL}/report`,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${AUTH_TOKEN}`
      },
      body: JSON.stringify({ domains: collected })
    });

    const result = JSON.parse(response.body);

    if (result.success) {
      // 清空本地存储
      $.setdata('[]', STORAGE_KEY);
      $.msg('域名收集器', `上报成功`, `新增 ${result.added} 个，总计 ${result.total} 个待分析`);
    } else {
      $.msg('域名收集器', '上报失败', result.error || '未知错误');
    }
  } catch (e) {
    $.msg('域名收集器', '上报失败', e.message || '网络错误');
  }
}

// 主入口
(async () => {
  if (typeof $request !== 'undefined') {
    // 请求时收集域名
    collectDomain();
  } else {
    // 定时任务上报
    await reportDomains();
  }
})()
.catch(e => $.logErr(e))
.finally(() => $.done({}));

// Env 类（QX 环境适配）
function Env(name) {
  this.name = name;
  this.logs = [];

  this.getdata = (key) => $prefs.valueForKey(key);
  this.setdata = (val, key) => $prefs.setValueForKey(val, key);

  this.msg = (title, subtitle, body) => {
    $notify(title, subtitle, body);
  };

  this.log = (...args) => {
    this.logs.push(args.join(' '));
    console.log(args.join(' '));
  };

  this.logErr = (e) => {
    this.log('ERROR:', e.message || e);
  };

  this.http = {
    post: (opts) => {
      return new Promise((resolve, reject) => {
        $task.fetch({
          method: 'POST',
          url: opts.url,
          headers: opts.headers,
          body: opts.body
        }).then(
          response => resolve(response),
          reason => reject(reason.error)
        );
      });
    }
  };

  this.done = (val = {}) => $done(val);
}
