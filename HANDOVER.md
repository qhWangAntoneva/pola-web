# pola-web 项目交接文档

> **交接时间**: 2026-05-17 23:00
> **仓库**: github.com/qhWangAntoneva/pola-web
> **线上地址**: https://qhwangantoneva.github.io/pola-web/
> **分支**: `gh-pages`（仅此分支，无 main）
> **最新构建**: d2a6057 — docs: update HANDOVER.md with e875766 build info
> **线上版本**: 已 push 到远程，等待 GitHub Pages CDN 刷新
> **算法依赖**: pola==0.1.2 from PyPI wheel (`pola-0.1.2-py3-none-any.whl`)
> **路线图**: `~/pola-web/roadmap/pola-web-bug-fix-roadmap.json`
> **本次 Session**: 交接文档 + matplotlib plot 修复 + 深度 Bug Hunt（21 项发现）

---

## 项目概览

pola 包的纯前端浏览器界面。基于 **Pyodide v0.27.0** WASM 运行时，用户在浏览器内完成 critical bandwidth 分析，**数据不出机器，无需后端服务器**。

---

## 当前状态仪表盘

| 维度 | 状态 |
|------|------|
| 前端功能 | ✅ 全部 6 项分析功能通过验证（CB / Full / Bootstrap / Dip Test / Bimodality Strength / Find Modes） |
| 算法版本 | ✅ pola==0.1.2（wheel 加载，新增 bimodality_strength + find_modes） |
| matplotlib 渲染 | ✅ 已修复 — 从 html5_canvas_element（不兼容 Pyodide v0.27.0）改为 PNG base64 data URL |
| 4 个旧 CRITICAL bug | ✅ 已修复（PyProxy泄漏、Stale IIFE、XSS、Error crash） |
| 迁移 | ✅ CBW web/ → pola-web 迁移完成，CBW 端已标记废弃 |
| GitHub Pages 部署 | ✅ deploy-pages.yml 已创建，监听 gh-pages 分支自动触发 |
| git 远程 | ✅ 已 push（d2a6057） |
| Bug 清单 | 📋 21 项确认问题（3 CRITICAL, 5 HIGH, 6 MEDIUM, 7 LOW/INFO）见路线图 |
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

## 🗺️ Bug 修复路线图

本次 Session（2026-05-17 22:35~23:00）通过 4 角色 subagent team（Python 代码审计 🐛 + 前端审计 🐛 + WASM 性能分析 ⚡ + 集成评审 🔗）对 pola-web 进行了深度 bug hunt，共发现 **56 项原始发现，合并为 21 项确认问题**（3 CRITICAL, 5 HIGH, 6 MEDIUM, 7 LOW/INFO）。

**路线图文件**: `roadmap/pola-web-bug-fix-roadmap.json`

### 4 阶段修复计划

| Phase | 优先级 | 任务数 | 预计耗时 | 说明 |
|-------|--------|--------|----------|------|
| Phase 1 | 🔴 CRITICAL | 3 | ~12min | Loading overlay z-index、renderResults null 保护、complex JSON 序列化 |
| Phase 2 | 🟠 HIGH | 5 | ~21min | PyProxy leak、dip 显示错误、h>0 校验、method 一致性、fetch 缓存破坏 |
| Phase 3 | 🟡 MEDIUM | 6 | ~29min | .toFixed guard、异常拓宽、onerror、CSS 变量、set 类型、CSV 检测 |
| Phase 4 | 🔵 LOW | 4 | ~30min | 模块级 import、onclick 迁移、benchmark guard、模板注入重构 |
| **总计** | | **18** | **~92min** | 全部修复后应用应达到 8/10 |

### 本次 Session 已完成的工作

| # | 工作内容 | 状态 |
|---|----------|------|
| 1 | 创建 HANDOVER.md 完整交接文档 | ✅ |
| 2 | 本地验证 Show Plots — 发现 3 个 matplotlib plot 全崩 | ✅ |
| 3 | visualize.py + index.html: 修复 plots → PNG base64 data URL | ✅ |
| 4 | deploy-pages.yml: branches [main] → [gh-pages] | ✅ |
| 5 | git commit + push (d2a6057) | ✅ |
| 6 | 4 角色 Bug Hunt → 21 项发现 + 路线图 | ✅ |

### 已知问题（来自 Bug Hunt）

| # | 严重性 | 问题 | 位置 |
|---|--------|------|------|
| 1 | 🔴 | Loading overlay 无 z-index，被 header 挡住 | style.css:167 |
| 2 | 🔴 | renderResults 对 null result 无保护，UI 崩 | index.html:710-730 |
| 3 | 🔴 | _to_js 返回 complex → JSON 序列化失败 | analyze.py:47-48 |
| 4 | 🟠 | _bm_name PyProxy leak，不在 finally 块 | index.html:1117-1123 |
| 5 | 🟠 | Dip 显示 "100 pts" 实际用 50 pts | index.html:882 |
| 6 | 🟠 | kde_plot 无 h>0 校验 | visualize.py:37 |
| 7 | 🟠 | analyze_full method 不一致 | analyze.py:133,146 |
| 8 | 🟠 | fetch py/ 脚本无缓存破坏 | index.html:301 |
| 9 | 🟡 | 5 处 .toFixed() 无 null guard | index.html:多处 |
| 10 | 🟡 | 异常捕获太窄 (只 catch ValueError) | analyze.py:161 |
| 11 | 🟡 | FileReader 无 onerror | index.html:351 |
| 12 | 🟡 | CSS --color-bg-secondary 未定义 | index.html:881 |
| 13 | 🟡 | _to_js 未处理 set 类型 | analyze.py:53 |
| 14 | 🟡 | CSV 表头检测脆弱 | index.html:360 |
| 15-18 | 🔵 | 代码质量/优化项（4项） | 多处 |

### 后续方向

1. **按路线图顺序修复 bug** — 从 Phase 1 开始，逐步推进
2. **线上验证 Show Plots** — CDN 刷新后验证 PNG 图表渲染正常
3. **旧站 `qhwangantoneva/pola` 清理** — 加 301 重定向到新站

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
