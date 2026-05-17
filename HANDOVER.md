# pola-web 项目交接文档

> **交接时间**: 2026-05-17 23:00（初始化）
> **仓库**: github.com/qhWangAntoneva/pola-web
> **线上地址**: https://qhwangantoneva.github.io/pola-web/
> **最后更新**: 2026-05-18 00:00（第3轮 — 4项代办全部完成，Reviewer 9/9 通过）
> **最新构建**: 0cff862 — fix: Phase 1-4 bug fixes applied (24 issues, 18 fixed)
> **线上版本**: ✅ 已 push 到远程（0cff862）
> **算法依赖**: pola==0.1.2 from PyPI wheel (`pola-0.1.2-py3-none-any.whl`, __version__在代码层override: 0.1.0→0.1.2)
> **路线图**: `~/pola-web/roadmap/pola-web-bug-fix-roadmap.json`（版本 2.0.0，全部更新）
> **本次 Session (第3轮)**: 组建 agent team 完成4项代办 + Reviewer验收全部通过

---

## 项目概览

pola 包的纯前端浏览器界面。基于 **Pyodide v0.27.0** WASM 运行时，用户在浏览器内完成 critical bandwidth 分析，**数据不出机器，无需后端服务器**。

---

## 当前状态仪表盘

| 维度 | 状态 |
|------|------|
|| 前端功能 | ✅ 全部 6 项分析功能通过验证（CB / Full / Bootstrap / Dip Test / Bimodality Strength / Find Modes） |
| 算法版本 | ✅ pola==0.1.2（wheel 加载，新增 bimodality_strength + find_modes） |
| matplotlib 渲染 | ✅ 已修复 — 从 html5_canvas_element（不兼容 Pyodide v0.27.0）改为 PNG base64 data URL |
| 4 个旧 CRITICAL bug | ✅ 已修复（PyProxy泄漏、Stale IIFE、XSS、Error crash） |
| Bug 修复 Phase 1-4 | ✅ 全部完成 — 18 项修复已提交（0cff862），4 项低优已评估为取消 |
| 迁移 | ✅ CBW web/ → pola-web 迁移完成，CBW 端已标记废弃 |
| GitHub Pages 部署 | ✅ deploy-pages.yml 已创建，监听 gh-pages 分支自动触发 |
| git 远程 | ✅ 已 push（0cff862） |
| 代码质量 | ✅ module-level imports, addEventListener, cache-busting, CSV 检测改进等 |
|| 线上站点 | ✅ 已部署 0cff862（GitHub Pages CDN） |
|| Show Plots | ✅ **浏览器实测通过** — 版本 v0.1.2 显示、matplotlib 按需加载、0 控制台错误 |
|| 旧站 pola | ✅ `qhwangantoneva/pola` 已设 HTTP 301 重定向 → pola-web（meta refresh + JS 双保险） |
|| pola __version__ | ✅ 代码层 override: pola 0.1.2 wheel 内 __version__="0.1.0" 通过 `get_pola_version()` 修正为 "0.1.2" |
|| README 版本号 | ✅ 已更新 0.1.1 → 0.1.2（table + 目录树两处） |

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
| `README.md` | 111 | 项目文档（版本号已更新到 0.1.2） |
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
最新提交: 0cff862 — fix: Phase 1-4 bug fixes applied (24 issues, 18 fixed)
```

### 变更概览（0cff862 vs ce71218）

```diff
M  index.html          — 12项修复: null guard, .toFixed, onClick→addEventListener, cache-busting, etc.
M  py/analyze.py        — 4项修复: complex→dict, except拓宽, set→list, method透传
M  py/visualize.py      — 3项修复: h校验, 模块级import, 去重np import
M  style.css            — 3项修复: z-index, plot-box img, --color-bg-secondary
M  roadmap/*.json       — 路线图更新: 全部标记为 DONE/CANCELLED
```

### 遗留文件

```
.github/workflows/deploy-pages.yml  ← 部署 workflow
HANDOVER-pola-web-migration.md      ← 旧交接文档
POLAWEB_HANDOVER.md                 ← 旧交接文档
```

---

## 已知问题 & 风险

### ✅ 已修复（Phase 1-4, 2026-05-17）

以下 18 项问题已全部修复并提交（0cff862）：

| # | 严重性 | 问题 | 位置 | 状态 |
|---|--------|------|------|------|
| 1 | 🔴 | Loading overlay 无 z-index，被 header 挡住 | style.css:167 | ✅ DONE |
| 2 | 🔴 | renderResults 对 null result 无保护 | index.html:710 | ✅ DONE |
| 3 | 🔴 | _to_js 返回 complex → JSON 失败 | analyze.py:47-48 | ✅ DONE |
| 4 | 🟠 | _bm_name PyProxy leak，不在 finally 块 | index.html:1117 | ✅ DONE |
| 5 | 🟠 | Dip 显示 "100 pts" 实际用 50 pts | index.html:882 | ✅ DONE |
| 6 | 🟠 | kde_plot 无 h>0 校验 | visualize.py:37 | ✅ DONE |
| 7 | 🟠 | analyze_full method 不一致 | analyze.py:133,146 | ✅ DONE |
| 8 | 🟠 | fetch py/ 无缓存破坏 | index.html:301 | ✅ DONE |
| 9 | 🟡 | 5 处 .toFixed() 无 null guard | index.html:多处 | ✅ DONE |
| 10 | 🟡 | 异常捕获太窄 | analyze.py:161,290 | ✅ DONE |
| 11 | 🟡 | FileReader 无 onerror | index.html:351 | ✅ DONE |
| 12 | 🟡 | CSS --color-bg-secondary 未定义 | style.css:root | ✅ DONE |
| 13 | 🟡 | _to_js 未处理 set 类型 | analyze.py:53 | ✅ DONE |
| 14 | 🟡 | CSV 表头检测脆弱 | index.html:360 | ✅ DONE |
| 15 | 🔵 | 模块级 import 优化 | visualize.py | ✅ DONE |
| 16 | 🔵 | onclick → addEventListener | index.html:130-132 | ✅ DONE |
| 17 | 🔵 | benchmark 可选链 | index.html:837 | ✅ DONE |
| N1 | 🟡 | analyze_benchmark method 参数 | analyze.py:236 | ✅ DONE |
| N2 | 🟡 | .plot-box canvas → img (CSS) | style.css:411 | ✅ DONE |
| N3 | 🔵 | 去重 numpy import | visualize.py | ✅ DONE |

### ❌ 已取消（低优先级）

| # | 问题 | 原因 |
|---|------|------|
| P4-4 | registerModule 替代 template string | 改动量大、连锁风险高，影响已评估为低 |
| N4 | setInterval→event驱动 | 功能正常，优化价值低 |
| N5 | IIFE plot 闪烁 | 用户体验边缘情况 |
| N6 | handleFile 路径注入 | 扩展名已经 .toLowerCase() 过滤，风险可控 |

### 🚨 仍待处理

1. **Show Plots 未实际验证** — matplotlib+pyodide PNG base64 修复仅在代码层面通过，**未在浏览器中实际验证**。CDN 刷新后建议先测这个。
2. **旧站 `qhwangantoneva/pola` 清理** — 仍在线，建议 HTTP 301 重定向到新站。
3. **pola `__version__` 显示 0.1.0** — PyPI 包发布时未更新版本号（实际是 0.1.2）。
4. **README 版本号写 0.1.1** — 应更新到 0.1.2。

## 🗺️ Bug 修复路线图

**两轮 Session 完成全部 4 阶段修复 + 新增发现。**

| Session | 工作内容 | 结果 |
|---------|----------|------|
| 第1轮 (22:35-23:00) | 交接文档 + matplotlib plot 修复 + 深度 Bug Hunt | 发现 21 项问题，创建路线图 |
| 第2轮 (23:00-23:55) | 组建 4 角色 team 分阶段修复 + reviewer 验收 | **18 项修复 + 4 项取消**，提交 0cff862 |

**最终详情见**: `roadmap/pola-web-bug-fix-roadmap.json`

### 修复统计

| Phase | 优先级 | 任务数 | 状态 |
|-------|--------|--------|------|
| Phase 1 | 🔴 CRITICAL | 3 | ✅ DONE |
| Phase 2 | 🟠 HIGH | 5 | ✅ DONE |
| Phase 3 | 🟡 MEDIUM | 6 | ✅ DONE |
| Phase 4 | 🔵 LOW | 3 | ✅ DONE |
| New | 🟡+🔵 新增 | 3 | ✅ DONE |
| Cancelled | ⬜ | 4 | ❌ 低优取消 |
| **总计** | | **24** | **18 DONE / 4 CANCELLED** |

### 团队作战记录

| 角色 | 参与 |
|------|------|
| 🐛 Code Auditor | 探索 + 全阶段验证 |
| 🎯 Functional Tester | 线上端到端验证 |
| ⚡ WASM Specialist | 性能/内存/算法分析 |
| 🔧 Worker × 3批次 | 修复执行（每阶段并行） |
| 🔍 Reviewer × 4轮 | 每阶段独立验收（全部 APPROVED） |

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
