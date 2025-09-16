# 自用规则自动化仓库
![更新状态](https://github.com/ipiggyzhu/rules/actions/workflows/convert.yml/badge.svg?branch=main)
![最后提交](https://img.shields.io/github/last-commit/ipiggyzhu/rules)

本仓库用于自动聚合、去重并生成适用于 **Loon** 与 **Quantumult X** 的自定义规则文件。

---

## ✨ 主要特性

*   **自动化聚合与更新**
    *   通过 GitHub Actions 每日定时拉取、去重、合并多个上游规则源。
    *   确保规则集始终保持最新状态。

*   **多平台支持**
    *   自动生成为 Loon 和 Quantumult X 两种工具优化过的、标准化的规则文件。

*   **精细化手动控制**
    *   **自定义黑名单**：通过 `manual/reject-rules.txt` 添加您自己的屏蔽规则（支持纯域名自动转换为后缀规则）。
    *   **自定义白名单**：通过 `manual/allow-rules.txt` 添加需要放行的域名，以修复误杀问题。
    *   **QX 专属规则**：通过 `manual/reject-rules-back.txt` 添加仅对 Quantumult X 生效的、格式更复杂的规则。

---

## 🚀 订阅与使用

您可以直接在您的 Loon 或 Quantumult X 配置中引用以下链接。链接指向 `main` 分支，会随着每日自动更新而保持最新。

### 广告拦截规则 (Ad Rules)

*   **For Loon:**
    ```
    https://raw.githubusercontent.com/ipiggyzhu/rules/main/Loon/ad-rules.list
    ```

*   **For Quantumult X:**
    ```
    https://raw.githubusercontent.com/ipiggyzhu/rules/main/QuantumultX/ad-rules.list
    ```

---

## 🛠️ 工作流

本仓库的核心工作流由 `.github/workflows/convert.yml` 文件定义，主要执行以下步骤：

1.  **定时触发**：每日凌晨定时启动。
2.  **拉取规则**：分别从为 Loon 和 Quantumult X 优选的上游规则列表中拉取最新的规则。
3.  **合并与去重**：将网络规则与 `manual/` 目录下的手动控制规则进行合并，并利用 `set` 进行高效去重。
4.  **格式化**：为两个平台分别进行严格的格式校验和标准化处理，确保兼容性。
5.  **推送更新**：将新生成的规则文件推送回本仓库的 `main` 分支。
