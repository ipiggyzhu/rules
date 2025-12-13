# 自用规则仓库

![更新状态](https://github.com/ipiggyzhu/rules/actions/workflows/update-rules.yml/badge.svg)
![最后更新](https://img.shields.io/github/last-commit/ipiggyzhu/rules?label=%E6%9C%80%E5%90%8E%E6%9B%B4%E6%96%B0)

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
- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) - Advertising
- [privacy-protection-tools/anti-AD](https://github.com/privacy-protection-tools/anti-AD)
- [Cats-Team/AdRules](https://github.com/Cats-Team/AdRules)
- [TG-Twilight/AWAvenue-Ads-Rule](https://github.com/TG-Twilight/AWAvenue-Ads-Rule)
- [limbopro/Adblock4limbo](https://github.com/limbopro/Adblock4limbo)

### 直连规则
- [blackmatrix7/ios_rule_script - ChinaMax](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Loon/ChinaMax) - 国内网站直连

## 自动更新

- **每日规则更新**: UTC 0:00（北京时间 08:00）自动运行
- **每月规则清理**: 每月1号自动检测并移除无效域名
- **Telegram 通知**: 更新后自动推送通知（需配置 Secrets）
