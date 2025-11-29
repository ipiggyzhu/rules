# AI 自动广告检测系统 - 配置指南

## 系统架构

```
圈X 收集域名 → Cloudflare Worker 存储 → GitHub Actions + AI 分析 → 自动更新规则
```

## 配置步骤

### 1. 部署 Cloudflare Worker

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 进入 **Workers & Pages** → **Create Application** → **Create Worker**
3. 给 Worker 命名（如 `domain-collector`）
4. 复制 `worker/domain-collector.js` 的内容到编辑器
5. 点击 **Save and Deploy**

**创建 KV 存储：**
1. 进入 **Workers & Pages** → **KV**
2. 创建命名空间，名称为 `DOMAINS`
3. 回到 Worker 设置 → **Settings** → **Variables**
4. 添加 KV 绑定：变量名 `DOMAINS`，选择刚创建的 KV

**设置环境变量：**
在 Worker **Settings** → **Variables** → **Environment Variables** 添加：
- `AUTH_TOKEN`: 自定义一个安全的密钥（如 `your-secret-token-123`）

### 2. 配置圈X脚本

在圈X配置文件中添加：

```ini
[rewrite_local]
# 收集访问的域名（按需开启，会略微增加耗电）
# ^https?:\/\/.+ url script-request-header https://raw.githubusercontent.com/ipiggyzhu/rules/main/scripts/domain-collector.js

[task_local]
# 每6小时上报一次域名
0 */6 * * * https://raw.githubusercontent.com/ipiggyzhu/rules/main/scripts/domain-collector.js, tag=域名上报, enabled=true
```

**配置脚本参数：**

方式一：使用 BoxJS
1. 安装 BoxJS（如果没有）
2. 找到"域名收集器"
3. 填入 Worker URL 和 Token

方式二：手动设置
在圈X中运行以下脚本设置参数：
```javascript
$prefs.setValueForKey('https://your-worker.workers.dev', 'domain_collector_url');
$prefs.setValueForKey('your-secret-token-123', 'domain_collector_token');
```

### 3. 配置 GitHub Secrets

在仓库 **Settings** → **Secrets and variables** → **Actions** 添加：

| Secret 名称 | 值 | 说明 |
|------------|-----|------|
| `WORKER_URL` | `https://your-worker.workers.dev` | Worker 地址 |
| `WORKER_TOKEN` | `your-secret-token-123` | 与 Worker 中设置的一致 |
| `AI_API_URL` | `https://api.xxx.com/v1` | 第三方 AI API 地址 |
| `AI_API_KEY` | `sk-xxx` | AI API 密钥 |
| `AI_MODEL` | `gpt-3.5-turbo` | 使用的模型（可选） |

### 4. 启用 GitHub Actions

确保仓库已启用 Actions，workflow 会：
- 每6小时自动运行
- 从 Worker 拉取收集的域名
- 使用 AI 分析是否为广告
- 自动更新 `sources/ad-blacklist.txt`
- 重新生成规则文件

## 工作流程

1. **日常使用**：你正常使用手机上网
2. **自动收集**：圈X 脚本在后台记录访问的域名
3. **定时上报**：每6小时自动上报到 Cloudflare Worker
4. **AI 分析**：GitHub Actions 每6小时运行，AI 判断哪些是广告域名
5. **自动更新**：确认的广告域名自动加入黑名单

## 处理误封

如果发现某个正常网站被误封：

1. 编辑 `sources/ad-whitelist.txt`
2. 添加被误封的域名（每行一个）
3. 提交更改，等待下次规则更新

## 手动触发分析

在 GitHub 仓库 **Actions** 页面，选择 **AI 域名分析** workflow，点击 **Run workflow**。

## 常见问题

**Q: 圈X 脚本耗电吗？**
A: rewrite 模式会略微增加耗电（因为每个请求都会触发脚本）。如果担心，可以只使用定时任务模式，手动添加可疑域名。

**Q: 第三方 AI API 推荐？**
A:
- 国内：通义千问、智谱AI 等都有免费额度
- 公益站：搜索"ChatGPT 公益站"或"AI 免费 API"

**Q: Worker 免费额度够用吗？**
A: Cloudflare Workers 免费版每天 100,000 次请求，绰绰有余。

**Q: 如何查看收集了多少域名？**
A: 访问 `https://your-worker.workers.dev/stats`（需要带 Authorization header）
