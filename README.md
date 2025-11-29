# 自用规则仓库

![更新状态](https://github.com/ipiggyzhu/rules/actions/workflows/update-rules.yml/badge.svg)

自动聚合生成 **Loon** 和 **Quantumult X** 广告拦截规则。

## 订阅链接

### 广告拦截规则
| 平台 | 链接 |
|------|------|
| Loon | `https://raw.githubusercontent.com/ipiggyzhu/rules/main/Loon/ad-rules.list` |
| Quantumult X | `https://raw.githubusercontent.com/ipiggyzhu/rules/main/QuantumultX/ad-rules.list` |

### 直连规则（国内网站）
| 平台 | 链接 |
|------|------|
| Loon | `https://raw.githubusercontent.com/ipiggyzhu/rules/main/Loon/direct-rules.list` |
| Quantumult X | `https://raw.githubusercontent.com/ipiggyzhu/rules/main/QuantumultX/direct-rules.list` |

## 目录结构

```
rules/
├── sources/              # 【手动编辑】源文件
│   ├── ad-blacklist.txt  # 广告黑名单（您添加的域名）
│   └── ad-whitelist.txt  # 白名单（防误杀）
│
├── Loon/                 # 【自动生成】Loon 规则
│   └── ad-rules.list
│
├── QuantumultX/          # 【自动生成】QX 规则
│   ├── ad-rules.list
│   └── QuantumultX.conf  # 配置文件
│
├── icons/                # 图标资源
│   ├── loon.json
│   ├── quantumultx.json
│   └── images/
│
└── converter.py          # 规则生成脚本
```

## 使用方法

### 添加广告域名

编辑 `sources/ad-blacklist.txt`，每行一个域名：

```
ad.example.com
tracker.example.com
```

### 添加白名单

编辑 `sources/ad-whitelist.txt`，每行一个域名：

```
example.com
```

### 本地运行

```bash
pip install requests
python converter.py
```

## 上游规则源

### 广告拦截
- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) - Advertising + PCDN
- [privacy-protection-tools/anti-AD](https://github.com/privacy-protection-tools/anti-AD)
- [Cats-Team/AdRules](https://github.com/Cats-Team/AdRules)

### 直连规则
- [blackmatrix7/ios_rule_script - ChinaMax](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Loon/ChinaMax) - 国内网站直连

## 自动更新

GitHub Actions 每天 UTC 0:00（北京时间 08:00）自动运行。

## AI 自动检测广告域名

本仓库支持 AI 自动检测广告域名功能：

1. 圈X 脚本自动收集你访问的域名
2. AI 分析并识别广告/追踪域名
3. 自动添加到黑名单

详细配置请参考 [AI 配置指南](docs/ai-setup.md)。
