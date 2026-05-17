# pola-web 项目交接文档

> **交接时间**: 2026-05-17 22:35
> **仓库**: github.com/qhWangAntoneva/pola-web
> **线上地址**: https://qhwangantoneva.github.io/pola-web/
> **分支**: `gh-pages`（仅此分支，无 main）
> **最新构建**: 31e756c — fix: _to_js() null bug + update pola wheel to 0.1.2
> **算法依赖**: pola==0.1.2 from PyPI wheel (`pola-0.1.2-py3-none-any.whl`)

---

## 项目概览

pola 包的纯前端浏览器界面。基于 **Pyodide v0.27.0** WASM 运行时，用户在浏览器内完成 critical bandwidth 分析，**数据不出机器，无需后端服务器**。

---

## 当前状态仪表盘

| 维度 | 状态 |
|------|------|
| 前端功能 | ✅ 全部 6 项分析功能通过验证（CB / Full / Bootstrap / Dip Test / Bimodality Strength / Find Modes） |
| 算法版本 | ✅ pola==0.1.2（wheel 加载，新增 bimodality_strength + find_modes） |
| matplotlib | ✅ 已修复 `loadPackage('matplotlib-pyodide')`（之前缺此行导致 canvas 空白） |
| 4 个 CRITICAL bug | ✅ 全部已修复（PyProxy泄漏、Stale IIFE、XSS、Error crash） |
| 迁移 | ✅ CBW web/ → pola-web 迁移完成，CBW 端已标记废弃 |
| GitHub Pages 部署 | ⚠️ deploy-pages.yml 已创建但**需创建 main 分支**才能触发 |
| 未提交变更 | ⚠️ 2 个文件未 commit（已删 INTEGRATION_REVIEW.md / 已改 index.html） |
| git 远程 | ⚠️ **从未 push 过** — gh-pages 分支为空远程 |
| 线上站点 | ✅ 当前在线，显示 pola web（从哪次构建上线待确认） |
| Show Plots | ⚠️ **未在浏览器中实际验证** |
| 旧站 pola | ❌ 旧站 `qhwangantoneva/pola` 仍在线，未清理/重定向 |

---

## 文件清单

| 文件 | 行数 | 说明 |
|------|------|------|
| `index.html` | 1142 | 主 SPA（HTML + CSS + JS），全部 JS 逻辑内联 |
| `style.css` | 579 | 全部样式（含深色模式 @media prefers-color-scheme） |
| `py/analyze.py` | 489 | Python 分析桥接层 — 6 个分析函数 + 工具函数 |
| `py/visualize.py` | 216 | matplotlib 绘图 — 3 种图表（KDE / Components / Sweep） |
| `py/__init__.py` | 0 | 空文件 |
| `pola-0.1.2-py3-none-any.whl` | — | 从 PyPI 下载的 pola wheel（WASM 兼容纯 Python） |
| `README.md` | 111 | 项目文档（README 仍写 pola 0.1.1） |
| `.github/workflows/deploy-pages.yml` | 27 | GitHub Pages 自动部署（监听 main 分支） |
| `.github/workflows/ci.yml` | — | 在 pola-web 中不存在，由 deploy-pages.yml 替代 |
| `.gitignore` | 9 | 忽略 pycache / venv / node_modules |
| `.nojekyll` | 0 | 跳过 Jekyll 处理 |
| `POLAWEB_HANDOVER.md` | 32 | 旧版交接文档（简单版） |
| `HANDOVER-pola-web-migration.md` | 69 | 旧版迁移交接（详细 — 迁移专项） |
| `HANDOVER.md` | — | **当前文件** — 完整项目交接 |

---

## 关键架构决策

### 1. pola 加载方式（最重要的决策）

```javascript
// 绕过 micropip（Pyodide v0.27.0 有 async race bug），
// 直接使用 pyodide.loadPackage() 加载本地 wheel 文件
await pyodide.loadPackage('./pola-0.1.2-py3-none-any.whl');
```

**为什么这样做**：pola 的 `Requires-Dist` 声明了 pdfplumber→pypdfium2（C++）、xlsx、xls、docx 等依赖，其中 `pypdfium2` 是 C++ 扩展，WASM 中没有可用 wheel。`micropip.install('pola')` 会在尝试解析依赖时挂死。改用 `pyodide.loadPackage(wheel)` 完全跳过 micropip，纯 Python wheel 直接被加载。

### 2. dip_test WASM 性能适配

`py/analyze.py` 中 dip_test 做了双重适配：
- subsample: n > 50 时随机下采样到 50（O(n²) 算法在 WASM 中极慢）
- cap: n_boot > 50 时截断到 50（p-value 精度 ~0.02，足够 α=0.05）

### 3. matplotlib 加载

```javascript
await pyodide.loadPackage('matplotlib');        // ~8MB
await pyodide.loadPackage('matplotlib-pyodide'); // HTML5 canvas backend
```

按需懒加载（`ensureMatplotlib()`），仅当用户勾选"Show Plots"且运行支持图表的分析类型时触发。

### 4. 数据解析策略

handleFile 函数采用**分级策略**：
1. **纯 JS 解析** `.csv /.tsv /.txt` — 不依赖 WASM
2. **回退到 pola.io** 复杂格式（XLSX/DOCX/PDF/HTML/JSON/Markdown） — 但 pola.io 需要 pypdfium2 等 WASM 不兼容依赖，实际**在 WASM 中不可用**

### 5. 安全保护

已在代码中应用 3 层保护：
- **PyProxy 生命周期管理**: try/finally + toJs() + destroy() 模式
- **Stale IIFE 保护**: `_renderVersion` counter 防止 async plot IIFE 污染过期 DOM
- **Error 前置检查**: renderResults 顶部检查 `result.error`

---

## Git 仓库状态

```
分支: gh-pages（仅有此分支）
远程: origin -> https://github.com/qhWangAntoneva/pola-web.git
```

### 未提交变更（2 文件）

```diff
- INTEGRATION_REVIEW.md（已删除 - 旧评审报告，清理完成）
+ index.html: 第 629 行新增 await pyodide.loadPackage('matplotlib-pyodide')
```

### 未跟踪文件（3 文件）

```
.github/workflows/deploy-pages.yml  ← 部署 workflow（需创建 main 分支才能用）
HANDOVER-pola-web-migration.md      ← 旧交接文档
POLAWEB_HANDOVER.md                 ← 旧交接文档
```

---

## 已知问题 & 风险

### 🚨 重要问题

1. **远程 gh-pages 为空** — 本地已提交的 hash（31e756c）从未 push 到 remote，远程线上站点显示的是旧版本。**这是最紧急的行动项。**

2. **deploy-pages.yml 监听 main 但仓库只有 gh-pages** — 需要创建 main 分支或修改 workflow。但 pola-web 所有内容在 gh-pages 分支（GitHub Pages 直接从此分支发布），所以是否需要 main 取决于工作流习惯。推荐：保持 gh-pages 为真相源，修改 workflow 也监听 gh-pages 或直接 manual dispatch。

3. **Show Plots 功能未实际测试** — matplotlib+pyodide 的 canvas 渲染仅在代码层面修复，**未在浏览器中实际验证**。

### 已知次要问题

| 问题 | 等级 | 说明 |
|------|------|------|
| pola `__version__` 显示 0.1.0（实际是 0.1.2） | 低 | PyPI 包发布时未更新版本号 |
| pola.io 在 WASM 中不可用 | 已接受 | 仅影响 XLSX/DOCX/PDF 上传（纯 JS 解析 CSV/TSV/JSON 正常工作） |
| README 版本号写 0.1.1 | 低 | 应更新到 0.1.2 |
| 旧站 `qhwangantoneva/pola` 仍在线 | 中 | 用户可能访问旧站，建议加 HTTP 301 重定向 |

---

## 后续可能方向

### 🔴 立即行动（未完成）

| # | 任务 | 优先级 | 说明 |
|---|------|--------|------|
| 1 | **commit + push 未提交变更** | 🔴 | `git add . && git commit -m "fix: add matplotlib-pyodide loadPackage"` |
| 2 | **确认线上版本** | 🔴 | push 后刷新 pola-web 检查 Pyodide 版本和 pola 版本 |
| 3 | **本地验证 Show Plots** | 🟠 | `python -m http.server 8000` → 浏览器打开 → 勾选 Show Plots → 运行 Full Analysis → 确认 canvas 渲染 |

### 🟠 中等优先级

| # | 任务 | 说明 |
|---|------|------|
| 4 | 创建 main 分支或修改 deploy workflow | 决定 pola-web 的工作流策略 |
| 5 | 旧站 `qhwangantoneva/pola` 加 301 重定向 | 在旧 repo 设置 GitHub Pages 重定向 |
| 6 | 更新 README 版本号 | 0.1.1 → 0.1.2 |
| 7 | CSV/TSV 上传的纯 JS 解析加强 | 当前先纯 JS 解析再 pola.io fallback，可进一步优化 |
| 8 | Bootstrap N 默认值设为 50 | 当前 UI bootstrap=50, nboot=99，快速样本加载时自动设为 50 |

### 🟢 远期优化

| # | 任务 | 说明 |
|---|------|------|
| 9 | Benchmark 并行运行 | 当前串行，数据量大时慢 |
| 10 | 移动端 tab sticky 定位调整 | header 换行时 sticky top 偏移 |
| 11 | 操作中状态反馈加强 | 按钮 disabled + loading spinner |
| 12 | pandas 样式结果显示表格 | 当前 HTML 表格，可加排序/筛选 |

---

## 关键技术细节

### 本地开发

```bash
cd ~/pola-web

# 启动服务器（WASM 需要正确 Content-Type）
python -m http.server 8000
# 浏览器访问: http://localhost:8000
```

### 更新 pola wheel

```bash
# 从 PyPI 下载新版
curl -LO https://pypi.org/packages/.../pola-X.Y.Z-py3-none-any.whl

# 更新 index.html 中的文件名
# 搜索 'pola-' 替换 pola-0.1.2 → pola-X.Y.Z
```

### 关键 API

| JS 函数 | 位置 index.html | 作用 |
|----------|----------------|------|
| `init()` | L231-296 | 主初始化：加载 Pyodide → numpy/scipy → pola wheel → Python 脚本 |
| `runAnalysis(type, params)` | L643-707 | 6 种分析的分发器 |
| `renderResults(type, result, params, showPlots)` | L710-1065 | 结果渲染 + plot 生成 |
| `ensureMatplotlib()` | L618-641 | 按需加载 matplotlib |
| `handleFile(file)` | L346-411 | 文件上传处理 |
| `_loadBenchmarks()` | L1083-1110 | 加载 benchmark 列表 |

| Python 函数 | 位置 analyze.py | 作用 |
|-------------|----------------|------|
| `analyze_critical_bandwidth()` | L64-107 | 单个 CB 分析 |
| `analyze_full()` | L110-164 | 完整分析（CB + trough + components） |
| `run_bootstrap()` | L167-211 | Bootstrap CI |
| `dip_test_analysis()` | L399-455 | Hartigan's dip test |
| `bimodality_strength_analysis()` | L357-396 | Bimodality 强度 |
| `find_modes_analysis()` | L296-354 | KDE 峰值检测 |
| `analyze_benchmark()` | L236-293 | Benchmark 案例分析 |

### 本地路径

```
~/pola-web/                           ← 项目根目录
~/Polarization-CBW/                   ← CBW 源码主仓库（web/ 已废弃）
~/roadmap/pola-web-migration-roadmap.json  ← 迁移路线图（已完成）
```

---

## 源仓库关系图

```
Polarization-CBW (ryZhangHason)
├── pola/                   ← Python 包源码（活跃开发中）
├── tests/                  ← 测试（237 tests, 96% coverage）
└── web/ [DEPRECATED]       ← 已废弃，指向 pola-web
    └── DEPRECATED.md       ← 标记迁移去向

pola-web (qhWangAntoneva)  [← 我们在这里]
├── index.html              ← 前端（修复版，功能正常）
├── py/analyze.py           ← Python 桥接（适配 pola 0.1.2 API）
├── py/visualize.py         ← matplotlib 绘图
├── pola-0.1.2-py3-none-any.whl  ← 算法来源
└── (GitHub Pages: https://qhwangantoneva.github.io/pola-web/)
```
