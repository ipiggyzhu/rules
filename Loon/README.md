# 自用Loon规则集

[![更新状态](https://img.shields.io/github/actions/workflow/status/ipiggyzhu/loon_rules/update_rules.yml?label=更新状态&style=flat-square)](https://github.com/ipiggyzhu/loon_rules/actions/workflows/update_rules.yml)
[![最后提交](https://img.shields.io/github/last-commit/ipiggyzhu/loon_rules?label=最后提交&style=flat-square)](https://github.com/ipiggyzhu/loon_rules/commits/main)

本目录用于自动生成和维护适用于 [Loon](https://www.loon.com/) 的自定义规则文件。

---

## ✨ 主要特性

*   **自动化聚合与每日更新**：通过 GitHub Actions 自动拉取、去重、合并多源规则。
*   **Loon标准格式输出**：所有规则均统一为Loon标准格式，便于直接订阅和使用。
*   **手动精准控制**：可通过 `manual/reject-rules.txt` 添加自定义黑名单，通过 `manual/allow-rules.txt` 精确移除误杀规则。

---

## 🚀 订阅与使用

建议使用 [jsDelivr CDN](https://www.jsdelivr.com/) 加速访问。

### 广告拦截规则

https://cdn.jsdelivr.net/gh/ipiggyzhu/loon_rules@main/Loon/ad-rules.txt

### 国内直连规则

https://cdn.jsdelivr.net/gh/ipiggyzhu/loon_rules@main/Loon/direct-rules.txt

---

## 🔧 自定义方法

- 编辑 `manual/reject-rules.txt`，可手动添加屏蔽域名。
- 编辑 `manual/allow-rules.txt`，可精确移除误杀规则（需完整匹配规则行）。

---

## 🛠️ 自动化流程

- 所有规则聚合、去重、格式转换均由 `converter.py` 自动完成。
- 工作流每日自动运行脚本，生成并推送最新规则文件。

---

## 来源致谢

本规则集聚合了以下优秀项目：

* privacy-protection-tools/anti-ad
* AdguardTeam/AdguardFilters
* sooyaaabo/Loon
* blackmatrix7/ios_rule_script
* 及其他社区贡献者

---

## 许可证

MIT © ipiggyzhu
