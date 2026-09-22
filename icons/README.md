# 图标订阅

## Loon

```
https://cdn.jsdelivr.net/gh/ipiggyzhu/rules@icons/loon.json
```

添加路径：配置 → 资源 → 订阅资源 → 右上角 `+` → 填入上述地址。

## Quantumult X

```
https://cdn.jsdelivr.net/gh/ipiggyzhu/rules@icons/quantumultx.json
```

手机端打开后点击图片可快捷添加。

## 为什么用 `icons` 分支而不是 `main`

jsDelivr 对单个「包」有 50 MB 上限，而一个包 = 一个仓库的一个 ref，不是单个文件。

`main` 分支被跟踪内容约 86.5 MB，其中两个 `ad-rules.list` 就占了约 68 MB。超过上限后
jsDelivr 只返回已经缓存过的文件，其余一律返回：

```
403 Package size exceeded the configured limit of 50 MB
```

表现出来就是一部分图标能显示、另一部分不能，且看起来毫无规律——图标本身没有问题，
是被同分支的大文件连累。

`icons` 是一个孤儿分支，根目录直接就是本目录的内容，包体约 15.3 MB，稳定低于上限。
同一批图片在 `main` 里仍然保留一份，两边互不影响。

## 增删图标后的发布流程

```bash
python scripts/fix_icon_manifests.py     # 重写清单里的 URL
python scripts/publish_icons_branch.py   # 重新生成 icons 分支（会校验包体是否仍低于 50 MB）
git push --force origin icons
```

随后刷新 CDN 缓存，客户端才能拿到新清单：

```bash
curl https://purge.jsdelivr.net/gh/ipiggyzhu/rules@icons/loon.json
curl https://purge.jsdelivr.net/gh/ipiggyzhu/rules@icons/quantumultx.json
```

## 规则订阅不要走 jsDelivr

`loon.lcf` 里的 `ad-rules.list` / `direct-rules.list` 使用 `raw.githubusercontent.com`，
这是有意为之：

- `ad-rules.list` 单文件 32 MB，本身就超过 jsDelivr 的 20 MB 单文件上限，会直接 403；
- 规则每天由 CI 更新，CDN 缓存会滞后。
