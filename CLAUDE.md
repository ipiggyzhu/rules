# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

iOS 代理应用（Loon 和 Quantumult X）的广告屏蔽规则聚合器。从多个上游源获取规则，与本地自定义合并，输出去重后的规则文件。

## 常用命令

```bash
# 本地生成规则
pip install requests
python converter.py

# 检查规则有效性（只报告）
python scripts/rule_checker.py

# 检查并自动清理无效域名
python scripts/rule_checker.py --clean
```

## 架构

```
上游源 (blackmatrix7, anti-AD, AWAvenue, Cats-Team, limbopro)
                    ↓
          converter.py (核心)
   - 带 3 次重试的 HTTP 请求
   - 合并 sources/ad-blacklist.txt
   - 过滤 sources/ad-whitelist.txt
   - 移除冗余子域名规则
   - IP-CIDR 自动添加 no-resolve
   - 转换为 Loon/QX 格式
   - 生成统计报告 (stats.json)
                ↙        ↘
    Loon/ad-rules.list   QuantumultX/ad-rules.list
```

## 关键文件

| 文件 | 用途 |
|------|------|
| `converter.py` | 规则聚合转换脚本 |
| `scripts/rule_checker.py` | 规则有效性检查（DNS 解析检测）|
| `sources/ad-blacklist.txt` | 手动添加的广告域名（可编辑）|
| `sources/ad-whitelist.txt` | 误杀白名单（可编辑）|
| `stats.json` | 运行统计数据（自动生成）|

## 规则格式映射

| Loon | Quantumult X |
|------|--------------|
| DOMAIN-SUFFIX | HOST-SUFFIX |
| DOMAIN-KEYWORD | HOST-KEYWORD |
| DOMAIN | HOST |
| IP-CIDR,x,no-resolve | IP-CIDR,x,no-resolve |

## 自动化

| Workflow | 触发时间 | 功能 |
|----------|----------|------|
| update-rules.yml | 每日 UTC 0:00 | 更新规则 |
| cleanup-rules.yml | 每月1号 UTC 2:00 | 清理无效域名 |

## GitHub Secrets 配置

| Secret | 用途 |
|--------|------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | 接收通知的 Chat ID |

## 优化特性

- **重试机制**: 上游源请求失败自动重试 3 次
- **子域名去重**: 自动移除被父域名覆盖的冗余规则
- **no-resolve**: IP-CIDR 规则自动添加，避免不必要的 DNS 查询
- **统计报告**: 输出各源贡献、去重数量、与上次对比
- **有效性检查**: 可检测域名是否仍可解析
- **Telegram 通知**: 成功/失败/去重数量推送

## 开发注意

- `Loon/` 和 `QuantumultX/` 下的文件是自动生成的，修改 `sources/` 目录
- 上游源配置在 `converter.py` 顶部
- 运行后会生成 `stats.json` 用于统计对比
