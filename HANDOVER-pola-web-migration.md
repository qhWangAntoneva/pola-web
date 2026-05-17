# pola-web 迁移 — 交接文档

> **交接时间**: 2026-05-17 22:10
> **项目**: pola-web 迁移 — CBW web/ → pola-web 独立仓库
> **当前状态**: 迁移完成，所有任务已验收

## 项目概览

将 Polarization-CBW 仓库中负责网站对接的所有文件（`web/` + 部署配置）迁移到 pola-web 独立仓库，使 pola-web 成为完全独立的 GitHub Pages 前端应用。CBW 仓库中 web/ 相关部分已废弃并停用。

## 新架构

```
Polarization-CBW (源码主仓库)          pola-web (独立部署仓库)
  pola/         ← Python 包源码          index.html      ← 前端主页面 (已修复matplotlib)
  tests/        ← 测试                    style.css       ← 样式表
  web/ ← 已废弃 (DEPRECATED.md)          py/analyze.py   ← Python桥接 (适配pola 0.1.2)
  deploy-pages.yml ← 已停用 (if: false)  py/visualize.py ← matplotlib绘图
  deploy-todo.md ← 已标记迁移             pola-0.1.2-py3-none-any.whl ← 算法来源
  README.md ← 链接已更新→pola-web         .github/workflows/deploy-pages.yml (新建)
                                          POLAWEB_HANDOVER.md (已更新)
                                          → deploy到 qhwangantoneva/pola-web gh-pages
                                          → https://qhwangantoneva.github.io/pola-web/
```

## 已完成的全部任务

| # | 任务 | 位置 | 说明 |
|---|------|------|------|
| A6 | 创建 deploy-pages.yml | pola-web/ | 监听 push to main, 部署到 pola-web gh-pages |
| A7 | 清理过渡文件 | pola-web/ | 删 INTEGRATION_REVIEW.md, 更新 POLAWEB_HANDOVER.md |
| C1 | 废弃标记 web/ | CBW/ | 创建 web/DEPRECATED.md |
| C2 | 更新网站链接 | CBW/README.md | pola → pola-web |
| C3 | 更新 CHANGELOG | CBW/CHANGELOG.md | 新增 v0.1.1 迁移条目 |
| C4 | 停用部署 workflow | CBW/.github/workflows/ | 添加 `if: false` |
| C5 | 标记 deploy-todo | CBW/deploy-todo.md | 顶部添加迁移通知 |
| D1 | 修复 matplotlib-pyodide | pola-web/index.html | ensureMatplotlib() 增加 loadPackage |

### 已通过 Reviewer 验收 (10/10)

所有 8 项变更已由独立的 Reviewer subagent 逐项审查，一次性通过、无修正项。

## 已知状态 & 注意事项

### pola-web 仓库
- **算法**: pola==0.1.2 from PyPI (pola-0.1.2-py3-none-any.whl)
- **Pyodide**: v0.27.0
- **可视化**: matplotlib + matplotlib-pyodide (已修复)
- **所有 4 个 CRITICAL bug** (PyProxy泄漏/Stale IIFE/XSS/Error crash) 在 pola-web 中**已全部修复**
- **已知问题**: pola 0.1.2 的 `__version__` 仍显示 `0.1.0` (PyPI 包发布版本号问题)
- **已知限制**: pdfplumber→pypdfium2 在 WASM 中不可用

### CBW 仓库
- web/ 目录内容保留但标记废弃
- deploy-pages.yml 已停用但保留配置（方便恢复）
- pola Python 包源码和 tests/ 正常不变

### 如果新 session 继续做
可能的后续方向：
1. **本地测试 Show Plots 功能** — 启动 `python -m http.server 8000` 在 pola-web 目录，手动验证 matplotlib 绘图渲染
2. **pola-web 仓库 git 初始化** — 如果还没建立本地 git 仓库，初始化并推送初始提交
3. **旧站 (qhwangantoneva/pola) 清理** — 旧站点仍在线，可考虑添加 redirect
4. **继续 pola(Polarization-CBW) 主库的开发** — CBW 主库的 Python 包开发仍在进行中

## 本地路径
- pola-web: `C:/Users/lenovos/pola-web/`
- CBW: `C:/Users/lenovos/Polarization-CBW/`
- 计划文件: `~/.hermes/plans/2026-05-17_2210-pola-web-migration.md`
- Roadmap: `~/roadmap/pola-web-migration-roadmap.json`
