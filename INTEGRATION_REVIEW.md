# pola-web 综合评审报告

## 1. 交叉验证结果

### 各报告发现交叉验证表

| # | 来源 | 发现 | 验证方式 | 结果 | 关联 |
|---|------|------|----------|------|------|
| A-1 | 🐛 Bug Hunter | PyProxy 内存泄漏 — loadQuickSample | 读代码 line 422 vs line 373-383 | ✅ **确认** | B-⚠️ 功能失败的**根本原因** |
| A-2 | 🐛 Bug Hunter | XSS — benchmark onclick | 读代码 line 974 | ✅ **确认** | 独立 |
| A-3 | 🐛 Bug Hunter | find_modes/bimodality 错误 → renderResults 崩溃 | 读代码 analyze.py:322-323, index.html:838-862 | ✅ **确认** | B-❌ 分析按钮无响应的**关联原因** |
| A-4 | 🐛 Bug Hunter | Async IIFE DOM 竞态 | 读代码 line 870-934 | ✅ **确认** | 合并入 C-1 |
| A-5 | 🐛 Bug Hunter | h_crit=0 falsy 陷阱 | 读代码 line 875 | ✅ **确认**（极低概率） | 独立 |
| A-6 | 🐛 Bug Hunter | _convert_result 无循环引用保护 | 读代码 analyze.py:50-56 | ⚠️ **部分确认**（实际影响极低） | 独立 |
| A-7 | 🐛 Bug Hunter | params.data 作为 PyProxy 传入 JSON.stringify | 读代码 line 422, 882, 901, 921 | ✅ **确认** | 与 A-1 同根，是 B 功能失败的**直接原因** |
| A-8 | 🐛 Bug Hunter | Tabs sticky top:57px 移动端不匹配 | 读代码 style.css:123 | ✅ **确认**（低严重性） | 独立 |
| A-9 | 🐛 Bug Hunter | analyze_benchmark 完整数据集 JSON 传输 | 读代码 analyze.py:267, index.html:994-995 | ✅ **确认** | 独立 |
| A-10 | 🐛 Bug Hunter | 未使用 CSS .result-value.muted | 读代码 style.css:393-395 | ✅ **确认** | 独立，无害 |
| A-11 | 🐛 Bug Hunter | Bootstrap distribution 无类型守卫 | 读代码 line 709 | ✅ **确认** | 独立 |
| A-12 | 🐛 Bug Hunter | Plot 失败静默 | 读代码 line 892-894, 912-914, 930-932 | ✅ **确认** | 与 A-4/C-1 共同加剧 UX 问题 |
| A-13 | 🐛 Bug Hunter | state._running 无加载反馈 | 读代码 line 434-520 | ✅ **确认** | 独立 |
| A-14 | 🐛 Bug Hunter | _to_js 未处理 np.float16/np.complex | 读代码 analyze.py:37-47 | ✅ **确认**（边缘情况） | 独立 |
| B-⚠️ | 🎯 Functional Tester | Quick Sample 无可见变化 | 分析代码 line 422-427 | ✅ **确认**（本质是 A-1 + A-7 因果链） | A-1 + A-7 |
| B-❌ | 🎯 Functional Tester | 所有 6 个分析按钮无响应 | 分析代码 line 434-520, 574-618 | ⚠️ **部分确认**（A-1 + A-7 问题，但 B 的自动化测试可能未触发 addEventListener） | A-1 + A-7 因果链 |
| C-1 | ⚡ WASM Specialist | Stale async IIFE cross-contamination | 读代码 line 870-934 | ✅ **确认** | 合并 A-4 + C-4 |
| C-2 | ⚡ WASM Specialist | Bootstrap 999 resamples 不设上限 | 读代码 line 89(max=999), analyze.py:189(min 999) | ⚠️ **修正**（有上限 999，但仍可能过重） | 独立 |
| C-3 | ⚡ WASM Specialist | CSV 上传依赖 WASM 不兼容 pola.io | 读代码 line 366-372 | ✅ **确认** | 独立 |
| C-4 | ⚡ WASM Specialist | Stale plot IIFE 在快速切换标签页 | 读代码 line 870-934 | ✅ **确认** | 合并入 C-1 |
| C-5 | ⚡ WASM Specialist | ensureMatplotlib 并发重复下载 | 读代码 line 550-563 | ✅ **确认** | 独立 |
| C-6 | ⚡ WASM Specialist | 上传临时文件在 Pyodide FS 累积 | 读代码 line 357-358 | ✅ **确认** | 独立 |
| C-7 | ⚡ WASM Specialist | Python 全局变量空间累计 | 读代码 line 422, 575-621 | ⚠️ **部分确认**（影响取决于使用次数） | 与 A-1 同类型内存问题 |
| C-8 | ⚡ WASM Specialist | dip_test subsample cap 50 限制统计功效 | 读代码 analyze.py:425-436 | ✅ **确认**（设计权衡） | 独立 |
| C-9 | ⚡ WASM Specialist | Brent vs Binary 在 WASM 中对比 | 代码层面无直接证据 | ⚠️ **信息性** | 独立 |
| C-10 | ⚡ WASM Specialist | WASM 可用内存 ~1.8GB | 环境信息 | ✅ **信息性** | 独立 |

### 发现合并

| 合并组 | 原始发现 | 合并原因 |
|--------|----------|----------|
| **CRIT-1** | A-1 + A-7 + B-⚠️ + B-❌ | A-1(内存泄漏) + A-7(JSON.stringify PyProxy) 共同导致 B 的"Quick Sample/分析按钮无响应" |
| **CRIT-2** | A-4 + C-1 + C-4 | 同一段代码(line 870-934)的同一 bug 被三个 Agent 独立发现 |
| **HIGH-1** | A-3 + B-❌(部分) | find_modes/bimodality 返回 error 后 JS 崩溃，是分析按钮无声失败的又一个原因 |

### 被驳斥/降级的发现

| 原始发现 | 裁决 | 理由 |
|----------|------|------|
| C-2 "999 不设上限" | ⚠️ **降级为 MEDIUM** | 代码实际有上限 (analyze.py:189 `min(n_resamples, 999)` + UI line 89 `max=999`)。999 对 >500 数据点仍可能导致长挂起，但不存在"无上限"问题。 |
| A-6 "循环引用保护" | ⚠️ **降级为 LOW** | 分析结果 dict 不可能包含循环引用（都是纯数据），递归深度有限。 |
| C-9 "Brent vs Binary" | ❌ **降级为 INFO** | 非 bug，是算法选择信息。 |

---

## 2. 最终问题列表（按优先级排序）

### 🔴 CRITICAL (4)

| ID | 严重性 | 描述 | 文件:行 | 影响评估 | 修复方案评估 |
|----|--------|------|---------|----------|-------------|
| **C1** | 🔴 CRITICAL | **PyProxy 内存泄漏 + 数据流断裂**：loadQuickSample 返回的 PyProxy 未 `.toJs()`/`.destroy()`，且直接作为 `currentData` 传入后续分析的 `JSON.stringify(params.data)`。 | index.html:422 / 574-621 / 882-921 | ⭐⭐⭐⭐⭐ **导致应用完全不可用**：Quick Sample 加载后 PyProxy 泄漏 WASM 内存，且后续分析按钮因 PyProxy 传入 JSON.stringify 失败。B 报告确认"所有按钮无响应"。 | **简单修复**：在 loadQuickSample 中将 `currentData = pyodide.runPython(code)` 改为 `currentData = pyodide.runPython(code).toJs()`。参考 handleFile (line 373-383) 已有正确模式。单行改动。 |
| **C2** | 🔴 CRITICAL | **Stale async IIFE plot cross-contamination**：renderResults 中的 fire-and-forget async IIFE (line 870-934) 在 DOM 被新 renderResults 替换后继续运行，将 plot canvas 追加到错误的结果页面。 | index.html:870-934 | ⭐⭐⭐⭐ **数据污染**：快速点击分析按钮 2-3 次后，plots 追加到错误 DOM，用户看到混乱结果。同时 pending Python 调用堆积。 | **中级修复**：给 renderResults 添加 cancellation token / version counter。在 IIFE 每次 DOM 操作前检查 token 是否仍有效。预计改动 ~20 行。 |
| **C3** | 🔴 CRITICAL | **XSS 注入 — benchmark onclick**：`${b.name}` 未经转义直接插入 onclick 属性。 | index.html:974 | ⭐⭐⭐⭐ **安全漏洞**：若 `b.name` 含单引号或特殊字符（来自 pola 包或 GH Pages API），可执行任意 JS。 | **简单修复**：对 b.name 做实体转义 `b.name.replace(/'/g, "\\'").replace(/"/g, '&quot;')`，或改用 addEventListener 绑定。单行改动。 |
| **C4** | 🔴 CRITICAL | **find_modes/bimodality 返回 error 时 renderResults 崩溃**：Python 返回 `{"error":"..."}` 但 JS 直接访问 `result.n_modes`、`result.modes.map()`。 | analyze.py:322-323,378-379 → index.html:838-862,802-834 | ⭐⭐⭐ **功能失效**：当 pola 版本缺少 find_modes/bimodality_strength 时，点击对应按钮导致 JS TypeError，用户看到空白结果。 | **简单修复**：在 renderResults 中添加 `if (result.error) { /* 显示错误消息 */ }` 前置检查。同时给 find_modes 和 bimodality 分支添加防御。~10 行。 |

### 🟠 HIGH (5)

| ID | 严重性 | 描述 | 文件:行 | 影响评估 | 修复方案评估 |
|----|--------|------|---------|----------|-------------|
| **H1** | 🟠 HIGH | **Bootstrap 999 resamples 导致 WASM 挂起**：UI 允许 Bootstrap N=999 (line 89) 和 Dip N Boot=9999 (line 101)。对 n>500 的数据，999 次 bootstrap 需 25+ 分钟。 | index.html:89,101 / analyze.py:189 | ⭐⭐⭐ **稳定性**：用户设置大值后浏览器标签页长时间无响应。 | **简单修复**：减小 UI 的 max 值（Bootstrap: 50-200，Dip: 99-999），或添加显式警告 text。也可在 JS 侧拦截大值。2 行改动。 |
| **H2** | 🟠 HIGH | **CSV 上传依赖 WASM 不兼容的 pola.io**：`from pola.io import read_data` 依赖 pypdfium2 C++、lxml 等原生扩展，WASM 中必失败。 | index.html:366-372 | ⭐⭐⭐ **功能失效**：CSV/XLSX/DOCX/PDF 文件上传后得到空数据结果，用户困惑。 | **简单修复**：先用纯 JS 解析 CSV/TSV/JSON，只对复杂格式回退 pola.io。对 CSV/TSV 可加纯 Python CSV 回退解析器。~30 行。 |
| **H3** | 🟠 HIGH | **state._running 无操作中状态反馈**：分析按钮有 `state._running` 锁防止重复提交 (line 434-520)，但无任何视觉反馈（无 spinner、按钮不变灰）。 | index.html:434-520 | ⭐⭐⭐ **UX**：用户点击分析按钮后无任何反应，可能再次点击（被 state._running 阻止），产生"按钮坏了"的错觉。 | **简单修复**：在 `state._running = true` 时禁用按钮并添加 loading text/spinner。在 finally 中恢复。~15 行。 |
| **H4** | 🟠 HIGH | **ensureMatplotlib 并发重复下载**：多个 async IIFE 可能同时调用 `pyodide.loadPackage('matplotlib')`，造成重复 8MB 下载。 | index.html:550-563 | ⭐⭐ **性能**：首次加载 matplotlib 时额外带宽浪费，边缘情况可能导致加载失败。 | **简单修复**：加 `state._loadingMpl` 锁，在加载完成前拒绝其他调用。~5 行。 |
| **H5** | 🟠 HIGH | **Plot 失败对用户静默**：所有 plot 生成错误被 `console.warn` 吞掉，用户看不到任何提示。 | index.html:892-894, 912-914, 930-932 | ⭐⭐ **UX**：matplotlib 加载失败或 Python 报错时，用户以为 plots 正常但看不到。 | **简单修复**：在 catch 中调用 `showError()` 或添加"Plot generation failed"占位提示。~6 行。 |

### 🟡 MEDIUM (5)

| ID | 严重性 | 描述 | 文件:行 | 影响评估 | 修复方案评估 |
|----|--------|------|---------|----------|-------------|
| M1 | 🟡 MEDIUM | **上传临时文件在 Pyodide FS 累积**：每次文件上传写入 `/tmp/upload.*` 但从不删除。 | index.html:357-358 | ⭐⭐ **内存**：长时间使用后 Pyodide FS 累积不必要文件。 | **简单修复**：在上传新文件前先 `pyodide.FS.unlink()` 旧文件。~3 行。 |
| M2 | 🟡 MEDIUM | **Python 全局变量空间从 runPython 累积**：每个分析调用在 Python 全局命名空间中创建 `_current_x` 等变量。 | index.html:422, 575-621 | ⭐ **内存**：长期运行后 Python 全局命名空间膨胀，但每次 runPython 覆盖同名变量。影响有限。 | **低优先级修复**：删除不再需要全局变量的模式，或运行后 clear。 |
| M3 | 🟡 MEDIUM | **Tabs 固定定位 top:57px 在移动端不匹配**：header 高度为 ~57px，但移动端换行后 header 更高，导致滚动时 tab 与 header 间有 gap。 | style.css:123 | ⭐⭐ **UI**：小屏设备用户体验降级。 | **简单修复**：使用 `position: sticky; top: 0;` 再加 `margin-top` 或动态计算 header 高度。 |
| M4 | 🟡 MEDIUM | **Bootstrap distribution 无类型守卫**：`result.distribution.slice(0, 20)` 未检查 result.distribution 是否存在。 | index.html:709 | ⭐⭐ **稳定性**：若 bootstrap 返回格式异常，JS 崩溃。 | **简单修复**：添加 `result.distribution && Array.isArray(result.distribution) ? ... : 'N/A'`。 |
| M5 | 🟡 MEDIUM | **analyze_benchmark 将完整数据集通过 JSON 传输**：`x.tolist()` 包含在 benchmark 结果中，序列化/反序列化两次。 | analyze.py:267 / index.html:994-995 | ⭐ **性能**：对大数据集浪费内存。JS 端立即 delete result.x。 | **低优先级**：改用 PyProxy 传递数据避免序列化。 |

### 🟢 LOW (5)

| ID | 严重性 | 描述 | 文件:行 |
|----|--------|------|---------|
| L1 | 🟢 LOW | h_crit=0 时 falsy 陷阱 (理论上) | index.html:875 |
| L2 | 🟢 LOW | _to_js 未处理 np.float16/np.complex 等 | analyze.py:37-47 |
| L3 | 🟢 LOW | dip_test subsample cap=50 限制统计功效 | analyze.py:425-436 |
| L4 | 🟢 LOW | 未使用的 CSS .result-value.muted | style.css:393-395 |
| L5 | 🟢 LOW | _convert_result 无循环引用保护 | analyze.py:50-56 |

---

## 3. 修复方案评估

### 🔴 C1 — PyProxy 内存泄漏 + 数据流断裂（**最优先**）

**改动文件**：`index.html`

**具体修改**：
```javascript
// 第 422 行（loadQuickSample 函数内）
// 原代码：
currentData = pyodide.runPython(code);
// 改为：
const _proxy = pyodide.runPython(code);
try {
  currentData = _proxy.toJs();
} finally {
  _proxy.destroy();
}
```

**注意事项**：
- 参考 handleFile (line 373-383) 已有完全相同的 try/finally 模式
- 确保 `currentData.slice(0, 20)` 和 `dataInput.value` 赋值仍在 try 块外或使用新的 currentData
- 此修复同时解决 A-7 (params.data 作为 PyProxy 传入 JSON.stringify) — 因为 currentData 变成纯 JS 数组后，JSON.stringify 正常工作

### 🔴 C2 — Stale async IIFE cross-contamination

**改动文件**：`index.html`

**具体修改**：
添加全局 counter：
```javascript
// 靠近 line 217，state 区域
state._renderVersion = 0;
```

在 renderResults 开头递增：
```javascript
// line 634
const renderVersion = ++state._renderVersion;
```

在 IIFE 每个 DOM 操作前检查：
```javascript
// line 885, 904, 923 - 每个 querySelector 前
if (state._renderVersion !== renderVersion) return; // stale, abort
```

**注意事项**：
- token 检查必须在 async await 之后、每个 DOM 操作之前
- 覆盖 3 个 plot 生成块
- 无需改动 Python 端

### 🔴 C3 — XSS 注入

**改动文件**：`index.html`

**具体修改**（第 974 行）：
```javascript
// 原代码：
`<button class="btn btn-secondary" onclick="app.runBenchmark('${b.name}')">Run</button>`
// 改为使用 addEventListener 或安全转义：
// 方案1（推荐）：生成 DOM 后用 addEventListener
const btn = document.createElement('button');
btn.className = 'btn btn-secondary';
btn.textContent = 'Run';
btn.addEventListener('click', () => app.runBenchmark(b.name));
// 方案2（最小改动）：转义
const safeName = b.name.replace(/'/g, "\\'").replace(/"/g, '&quot;');
`<button class="btn btn-secondary" onclick="app.runBenchmark('${safeName}')">Run</button>`
```

### 🔴 C4 — Error response crash

**改动文件**：`index.html`（renderResults 函数）

**具体修改**：
```javascript
// 在 line 634 后，renderResults 函数开头添加：
function renderResults(type, result, params, showPlots) {
  // --- 新增：错误检查 ---
  if (result && result.error) {
    resultsContent.innerHTML = `<div class="error-alert">${result.error}</div>`;
    document.querySelector('[data-tab="results"]').click();
    return;
  }
  // ... 原有代码
```

同时为 modes (line 838) 和 bimodality (line 803) 分支各自加类型守卫：
```javascript
if (type === 'modes') {
  if (!result.modes || !Array.isArray(result.modes)) {
    html.push('<div class="error-alert">No mode data available.</div>');
  } else {
    // ... 原有代码
  }
}
```

### 🟠 H1 — Bootstrap 大值导致挂起

**改动文件**：`index.html` line 89, 101

**具体修改**：
```html
<!-- 原代码 -->
<input ... id="param-bootstrap" type="number" value="99" min="10" max="999" step="10">
<!-- 改为 -->
<input ... id="param-bootstrap" type="number" value="50" min="10" max="200" step="10">

<!-- 原代码 -->
<input ... id="param-nboot" type="number" value="999" min="99" max="9999" step="100">
<!-- 改为 -->
<input ... id="param-nboot" type="number" value="99" min="10" max="999" step="10">
```

或添加用户端警告。

### 🟠 H2 — CSV 上传 pola.io 失败

**改动文件**：`index.html` + 可选的 `py/io_helpers.py`

**修复思路**：
1. 在 handleFile 中先用 JS 解析纯文本格式（CSV, TSV, JSON, TXT）
2. 只对 XLSX/DOCX/PDF 等复杂格式尝试 pola.io
3. 或写一个纯 Python CSV 解析器在 WASM 侧

```javascript
// index.html handleFile 内新增
async function parseFileLocally(file, ext) {
  if (ext === '.csv' || ext === '.tsv' || ext === '.txt') {
    const text = await file.text();
    // 简单 CSV 解析
    const lines = text.trim().split('\n').slice(1); // skip header
    const numbers = lines.flatMap(line => 
      line.split(ext === '.tsv' ? '\t' : ',').map(Number).filter(v => !isNaN(v))
    );
    if (numbers.length > 0) return numbers;
  }
  // 回退到 pola.io
  return null;
}
```

### 🟠 H3 — 无操作中状态反馈

**改动文件**：`index.html`

**修改示例**（以 btn-analyze-cb 为例）：
```javascript
// 在每个分析按钮 handler 中：
state._running = true;
$('btn-analyze-cb').disabled = true;
$('btn-analyze-cb').textContent = 'Analyzing…';
updateStatus('loading', 'Running analysis…');
try {
  // ... 原有分析代码
} finally {
  state._running = false;
  $('btn-analyze-cb').disabled = false;
  $('btn-analyze-cb').textContent = 'Analyze Critical Bandwidth';
  updateStatus('ready', 'Ready');
}
```

---

## 4. 建议修复顺序

### 第一阶段：🔴 紧急修复（立即 —— 本周）
| 顺序 | ID | 修复 | 改动量 | 风险 |
|------|----|------|--------|------|
| 1 | C1 | loadQuickSample 中 `.toJs()` + `.destroy()` | 4 行 | 低（有 handleFile 参考实现） |
| 2 | C3 | XSS 转义 | 1-3 行 | 极低 |
| 3 | C4 | renderResults 添加 error 前置检查 | 8 行 | 低 |

### 第二阶段：🟠 高优修复（本周 —— 下周）
| 顺序 | ID | 修复 | 改动量 | 风险 |
|------|----|------|--------|------|
| 4 | C2 | stale IIFE + cancellation token | 20 行 | 中等（需理解 async flow） |
| 5 | H1 | Bootstrap UI max 值调低 | 2 行 | 极低 |
| 6 | H2 | CSV 上传纯 JS 解析 fallback | 30 行 | 低 |
| 7 | H3 | 操作中状态反馈 | 15 行 | 低 |

### 第三阶段：🟡🟢 常规/优化修复（下周 —— 下月）
| 顺序 | ID | 修复 | 改动量 |
|------|----|------|--------|
| 8 | H4 | ensureMatplotlib 并发锁 | 5 行 |
| 9 | H5 | Plot 失败用户可见提示 | 6 行 |
| 10 | M1 | 上传临时文件清理 | 3 行 |
| 11 | M3 | 移动端 tab sticky 修复 | 3 行 |
| 12 | M4 | Bootstrap distribution 类型守卫 | 2 行 |
| 13 | M2 | Python 全局变量清理 | 2 行 |
| 14 | M5 | benchmark 数据传递优化 | 5 行 |
| 15 | L1-L5 | 低优先级问题 | 合计 ~15 行 |

---

## 5. 总体评分

### 总体评分：**4.5 / 10**

**扣分明细**：
| 类别 | 扣分 | 理由 |
|------|------|------|
| 功能性 | **-2.5** | C1 导致 Quick Sample + 分析按钮基本不可用（B 报告验证） |
| 安全性 | **-1.5** | C3 XSS 漏洞，应用可被完全攻陷 |
| 稳定性 | **-1.0** | C2 stale IIFE、C4 error crash、H1 bootstrap 挂起 |
| UX | **-1.0** | H3 无操作反馈、H5 无声失败、M3 移动端异 |
| 内存 | **-0.5** | A-1 PyProxy 泄漏、C-6 FS 累积、C-7 全局变量 |

**优点**：
- ✅ 应用架构清晰（Pyodide + pola 集成）
- ✅ 代码组织良好（JS/Python 分离清晰）
- ✅ Benchmark 系统设计精巧
- ✅ 多数问题修复路径明确、改动量小

**关键结论**：
1. **最关键的 bug 是 C1**（PyProxy 未 toJs）—— 这是一个 4 行修复，但直接导致整个应用不可用
2. **安全漏洞 C3** 虽不影响功能，但影响所有使用该页面的用户
3. **所有 CRITICAL 问题都有简单修复方案**（均 < 20 行改动）
4. 第一阶段修复后应用应能达到 **7/10**
