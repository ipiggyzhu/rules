# 自用Loon规则集

[![更新状态](https://img.shields.io/github/actions/workflow/status/ipiggyzhu/loon_rules/update_rules.yml?label=更新状态&style=flat-square)](https://github.com/ipiggyzhu/loon_rules/actions/workflows/update_rules.yml)
[![最后提交](https://img.shields.io/github/last-commit/ipiggyzhu/loon_rules?label=最后提交&style=flat-square)](https://github.com/ipiggyzhu/loon_rules/commits/main)

这是一个用于自动生成和维护 [Loon](https://www.loon.com/) 代理工具自定义规则的仓库。

---

## ✨ 主要特性

*   **每日自动更新**：通过 GitHub Actions 每日定时更新，确保规则的时效性。
*   **聚合优质源**：聚合了多个社区流行的、高质量的规则源。
*   **去重与标准化**：自动去重合并，并将所有规则统一为干净、无策略的Loon标准格式。
*   **手动精准控制**：通过 `manual/` 目录下的 `reject-rules.txt` 和 `allow-list.txt`，您可以轻松添加自定义规则，或精确移除任何不需要的规则，防止误杀。

---

## 🚀 如何使用 (订阅链接)

建议使用 [jsDelivr CDN](https://www.jsdelivr.com/) 加速访问，以获得最佳的下载速度和稳定性。

### 广告拦截规则 (ad-rules.list)

用于拦截各类应用及网页中的广告、跟踪器和分析请求。在 Loon 中，建议为此规则集配置 **REJECT** 策略。

https://cdn.jsdelivr.net/gh/ipiggyzhu/loon_rules@main/ad-rules.list

### 国内直连规则 (direct-rules.list)

包含常见的国内网站、应用、CDN以及苹果在中国的服务等。建议为此规则集配置 **DIRECT** 策略。

https://cdn.jsdelivr.net/gh/ipiggyzhu/loon_rules@main/direct-rules.list

---

## 🔧 如何自定义

本仓库的核心优势在于其高度的可定制性，您可以通过编辑 `manual/` 目录下的文件来精准控制最终的规则列表：

### 添加自定义屏蔽规则
编辑 `manual/reject-rules.txt` 文件，将您想手动添加的屏蔽规则（遵循Loon格式）写入其中即可。此文件中的所有规则都会被自动合入最终的 `ad-rules.list`。

### 移除不想用的规则 (白名单)
编辑 `manual/allow-list.txt` 文件。当您发现 `ad-rules.list` 中有某条规则导致网站或App无法正常使用时，只需将那条**【完整的规则】**复制并粘贴到此文件中，一行一条。工作流在下次运行时，会自动将这些规则从最终列表中精确移除。

**示例 `allow-list.txt`:**
下面这两行规则将在生成最终列表时被精确移除

```
bing.com
DOMAIN-SUFFIX,bing.com,cn.bing.net
```

---

## 🛠️ 自动化流程

本仓库采用两个独立的、按时序执行的 GitHub Actions 工作流，以确保流程的稳定和清晰：

1.  **转换工作流 (`convert.yml`)**
    - **触发**：每日 `07:30` (北京时间) 定时运行。
    - **任务**：负责从上游拉取非标准格式的规则（如 AdGuard Home 格式），通过 `converter.py` 脚本将其清洗、转换为统一的 Loon 规则，并保存到 `generated/` 目录中。

2.  **聚合工作流 (`update_rules.yml`)**
    - **触发**：在转换工作流完成之后，检查转换工作流是否执行完成来触发聚合任务的执行。
    - **任务**：这是生成最终规则的核心步骤。它会：
        1.  读取 `generated/` 中的转换结果。
        2.  聚合所有外部优质规则源。
        3.  添加您在 `manual/reject-rules.txt` 中定义的个人规则。
        4.  使用 `manual/allow-list.txt` 作为白名单，对聚合后的所有规则进行**精确整行过滤**，移除您指定的规则。
        5.  最后，对结果进行去重和排序，生成根目录下的 `ad-rules.list` 和 `direct-rules.list` 文件并推送回仓库。

---

## 来源致谢

本规则集聚合和处理了以下优秀的开源项目，感谢原作者们的辛勤付出：

*   [privacy-protection-tools/anti-ad](https://github.com/privacy-protection-tools/anti-ad)
*   [AdguardTeam/AdguardFilters](https://github.com/AdguardTeam/AdguardFilters)
*   [sooyaaabo/Loon](https://github.com/sooyaaabo/Loon)
*   [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)
*   以及其他社区贡献者。

---

## 许可证

[MIT](https://choosealicense.com/licenses/mit/) © ipiggyzhu
