<h1 align="center">学习通 PPT 辅助下载</h1>

<p align="center"><img src="docs/logo.png" alt="Logo" title="Logo" /></p>

<p align="center">
基于 <code>requests</code> 爬取学习通课件 PPT 图片并转换为 PDF 的辅助工具，提供可视化 GUI 和命令行两种使用方式。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/requests-2.32.3-blue?logo=python" alt="requests">
  <img src="https://img.shields.io/badge/fpdf2-2.8.1-orange?logo=python" alt="fpdf2">
  <img src="https://img.shields.io/badge/Pillow-11.0.0-brightgreen?logo=python" alt="Pillow">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-brightgreen" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-orange" alt="License">
</p>

<p align="center">
  <a href="https://github.com/freeShao/Learning-action">
    <img src="https://repobeats.axiom.co/api/embed/7fc17684308aa1ab89d08e771e2355548bf8fb59.svg" />
  </a>
</p>

---

## 功能

- **下载**：抓取学习通课件每页预渲染图片
- **合并**：将下载的图片合成为单个 PDF 文件
- **GUI 操作**：图形界面，输入 URL 即可一键下载
- **CLI 操作**：命令行脚本，适合批量 / 自动化场景
- **自动页数检测**：填入 URL 后一键识别课件总页数
- **缓存管理**：清理已下载的临时图片文件夹

## 获取基础 URL

1. 浏览器打开学习通课程 → 进入 **章节** → 点击 **课时** 内的 PPT 预览
2. 按 **F12** 打开开发者工具 → **网络(Network)** 面板 → 筛选 `1.png`
3. 在请求列表中找到 `1.png`，复制其完整 URL
4. 删掉末尾的 `1.png`，只保留到 `thumb/` 为止

```
# 示例（完整）
https://s3.ananas.chaoxing.com/sv-w7/doc/51/18/e4/127ef24fab63d580372a890efd5dc250/thumb/1.png

# 提取的基础 URL（删掉 1.png）
https://s3.ananas.chaoxing.com/sv-w7/doc/51/18/e4/127ef24fab63d580372a890efd5dc250/thumb/
```

## 安装

```bash
pip install requests fpdf2 pillow
```

## 使用

### GUI 模式（推荐）

```bash
python xuexitong-ppt-download-gui.py
```

1. 粘贴基础 URL 到输入框
2. 点击 **检测页数** 自动获取总页数
3. 确认页码和文件名
4. 点击 **开始下载**

### CLI 模式

```bash
python xuexitong-ppt-download.py
```

根据脚本内提示输入 URL 与页码范围。

## 输出结构

```
xuexitong_script/
├── images/                     # 缓存：按文件名归类的原始图片
│   └── <文件名>/
│       ├── 1.png
│       ├── 2.png
│       └── ...
├── out_pdf/                    # 生成的 PDF 文件
│   └── <文件名>.pdf
└── docs/
    └── logo.png                # 应用图标
```

## 独立打包

如需分发给没有 Python 环境的 Windows 用户，可用 PyInstaller 打包为单文件 exe：

```bash

```

产物在 `dist/xuexitong-ppt-download.exe`，约 **15~20 MB**。

也可通过 GitHub Actions 自动构建：推送 `xuexitong-*` 标签即触发打包并发布到 Release。

## 依赖

| 包 | 版本 | 用途 |
|---|---|---|
| requests | >= 2.32.3 | HTTP 请求下载图片 |
| fpdf2 | >= 2.8.1 | 图片合成 PDF |
| Pillow | >= 11.0.0 | 图片尺寸检测 |
| tkinter | （Python 内置） | GUI 界面 |

---
