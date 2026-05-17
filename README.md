# pola-web 🧮

> **pola 包的浏览器前端** — 基于 Pyodide WASM 的纯前端 critical bandwidth 分析工具

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-live-brightgreen)](https://qhwangantoneva.github.io/pola-web/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**在线演示**: https://qhwangantoneva.github.io/pola-web/

---

## 📖 项目简介

pola-web 是 [pola](https://pypi.org/project/pola/) Python 包的浏览器端界面。用户可以通过拖放或粘贴数据，在浏览器内（通过 Pyodide WASM）完成 bimodal 分布的 **critical bandwidth** 分析，所有计算在本地完成，数据不出机器。

无需安装 Python、无需后端服务器、无需 npm 构建工具 — 纯静态站点，直接通过 GitHub Pages 部署。

---

## ✨ 功能特性

- **📥 拖放粘贴数据** — 支持 CSV/TSV 文件上传或手工粘贴（逗号、空格、换行分隔）
- **📊 3 个预设样本** — Well-Separated Bimodal / Barely Separated / Unimodal 快速体验
- **🔬 Critical Bandwidth 分析** — 计算双峰分离的临界带宽，支持多种 kernel（Gaussian/Epanechnikov/Uniform/Triangular）和搜索方法（Binary/Brent）
- **📈 Full Analysis** — 一次性获取 CB + trough 检测 + 分量分解 + bandwidth sweep 可视化
- **🔄 Bootstrap 分析** — 通过 Bootstrap 重采样获取 critical bandwidth 的置信区间
- **⏱ Benchmark 套件** — 12 个预定义 benchmark case 验证分析精度
- **🎨 内联图表** — matplotlib 渲染的 KDE/分量/带宽扫描图（可选关闭以加速）
- **🌙 深色模式** — 自动跟随系统主题
- **📱 响应式设计** — 桌面与移动端均可使用

---

## 🚀 快速使用

1. **打开页面**: https://qhwangantoneva.github.io/pola-web/
2. **等待加载**: Pyodide + Python 科学计算库 (~9s 首次加载)
3. **选择数据**: 点击预设样本、拖放文件、或粘贴数据到文本框
4. **运行分析**: 点击 CB / Full / Bootstrap 按钮查看结果
5. **Benchmark**: 切换到 Benchmark 标签运行预设测试

---

## 🛠 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| [Pyodide](https://pyodide.org/) | v0.27.0 | WASM Python 运行时 |
| [pola](https://pypi.org/project/pola/) | 0.1.2 | 核心计算库（critical bandwidth） |
| numpy + scipy | Pyodide 内置 | 科学计算 |
| matplotlib | Pyodide 内置 (可选) | 图表渲染 (~8MB) |
| 前端 | 原生 HTML/CSS/JS | 无框架、无构建工具 |

---

## 💻 本地开发

```bash
# 克隆仓库
git clone https://github.com/qhWangAntoneva/pola-web.git
cd pola-web

# 启动本地 HTTP 服务器
python -m http.server 8000

# 浏览器访问
open http://localhost:8000
```

> ⚠️ 注意：WASM 需要 `Content-Type` 正确设置，部分简单静态服务器可能不兼容。推荐使用 `python -m http.server`。

---

## 🚢 部署

部署到 GitHub Pages 即可：

```bash
# 推送 gh-pages 分支
git push origin gh-pages

# GitHub Actions CI/CD 会自动触发部署
```

GitHub Pages 对 `gh-pages` 分支自动发布。项目已配置 `.github/workflows/ci.yml` 进行健康检查。

---

## 📁 项目结构

```
~/pola-web/
├── index.html                 # 主 SPA (HTML + CSS + JS)
├── style.css                  # 全部样式（含深色模式）
├── pola-0.1.2-py3-none-any.whl  # pola wheel (本地静态文件)
├── py/
│   ├── analyze.py             # Python 桥接层（核心）
│   ├── visualize.py           # matplotlib 图表渲染
│   └── __init__.py            # 空文件
├── .github/workflows/
│   └── ci.yml                 # GitHub Actions 部署
├── .gitignore
├── .nojekyll                  # 跳过 Jekyll 处理
└── README.md                  # 本文件
```

---

## 📄 License

MIT
