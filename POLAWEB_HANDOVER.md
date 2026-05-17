# pola-web Handover

## 当前状态 (2026-05-17)

### 已完成
- ✅ **Bug 修复**: `_to_js()` 缺少普通 Python 类型兜底 → 所有分析功能恢复
- ✅ **Wheel 更新**: pola 0.1.0 → 0.1.2 (从 PyPI 下载)，新增 `bimodality_strength` + `find_modes`
- ✅ **所有 6 项功能验证通过**
- ✅ **迁移完成**: CBW web/ → pola-web 独立仓库
- ✅ **matplotlib-pyodide 修复**: 已添加 `loadPackage('matplotlib-pyodide')`

### 仓库架构
- **源码仓库**: `qhwangantoneva/pola-web` (此仓库)
- **部署仓库**: 同仓库的 `gh-pages` 分支
- **线上地址**: https://qhwangantoneva.github.io/pola-web/
- **算法来源**: `pola==0.1.2` from PyPI wheel (`pola-0.1.2-py3-none-any.whl`)
- **旧 CBW 仓库**: `web/` 目录已废弃，部署 workflow 已停用

### 关键文件
| 文件 | 说明 |
|------|------|
| `index.html` | 主页面，JS 逻辑 (1141 行) |
| `py/analyze.py` | Python 分析桥接层 (489 行) |
| `py/visualize.py` | matplotlib 绘图桥接层 (216 行) |
| `style.css` | 样式表 |
| `pola-0.1.2-py3-none-any.whl` | 从 PyPI 下载的 pola wheel |
| `.github/workflows/deploy-pages.yml` | GitHub Pages 自动部署 |

### 已知问题
- pola 0.1.2 的 `__version__` 仍显示 `0.1.0` (PyPI 包发布时未更新)
- `pola.io` 的 pdfplumber / pypdfium2 在 WASM 中不可用（已知限制）
- HTTP server: `python -m http.server 8000`
