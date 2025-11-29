/**
 * Cloudflare Worker - 域名收集器
 *
 * 功能：
 * 1. 接收来自 QX 的域名上报
 * 2. 存储到 KV 中（去重）
 * 3. 提供 API 供 GitHub Actions 拉取
 *
 * 部署步骤：
 * 1. 在 Cloudflare Dashboard 创建 Worker
 * 2. 创建 KV namespace，绑定为 DOMAINS
 * 3. 设置环境变量 AUTH_TOKEN（用于验证）
 * 4. 部署此代码
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const authToken = request.headers.get('Authorization');

    // 验证 token
    if (authToken !== `Bearer ${env.AUTH_TOKEN}`) {
      return new Response('Unauthorized', { status: 401 });
    }

    // POST /report - QX 上报域名
    if (request.method === 'POST' && url.pathname === '/report') {
      try {
        const data = await request.json();
        const domains = data.domains || [];

        if (!Array.isArray(domains) || domains.length === 0) {
          return Response.json({ error: 'No domains provided' }, { status: 400 });
        }

        // 获取现有域名
        const existing = await env.DOMAINS.get('pending', { type: 'json' }) || [];
        const existingSet = new Set(existing);

        // 添加新域名（去重）
        let added = 0;
        for (const domain of domains) {
          const cleaned = domain.toLowerCase().trim();
          if (cleaned && !existingSet.has(cleaned)) {
            existingSet.add(cleaned);
            added++;
          }
        }

        // 保存
        await env.DOMAINS.put('pending', JSON.stringify([...existingSet]));

        return Response.json({
          success: true,
          added: added,
          total: existingSet.size
        });
      } catch (e) {
        return Response.json({ error: e.message }, { status: 500 });
      }
    }

    // GET /domains - GitHub Actions 拉取域名
    if (request.method === 'GET' && url.pathname === '/domains') {
      const domains = await env.DOMAINS.get('pending', { type: 'json' }) || [];
      return Response.json({ domains: domains, count: domains.length });
    }

    // POST /clear - 清空已处理的域名
    if (request.method === 'POST' && url.pathname === '/clear') {
      await env.DOMAINS.put('pending', JSON.stringify([]));
      return Response.json({ success: true, message: 'Cleared' });
    }

    // GET /stats - 统计信息
    if (request.method === 'GET' && url.pathname === '/stats') {
      const domains = await env.DOMAINS.get('pending', { type: 'json' }) || [];
      const processed = await env.DOMAINS.get('processed_count') || '0';
      return Response.json({
        pending: domains.length,
        processed: parseInt(processed)
      });
    }

    return new Response('Domain Collector API\n\nEndpoints:\nPOST /report - Report domains\nGET /domains - Get pending domains\nPOST /clear - Clear pending\nGET /stats - Statistics', {
      status: 200,
      headers: { 'Content-Type': 'text/plain' }
    });
  }
};
