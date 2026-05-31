# Learning-action
学习使用 GitHub Action 功能测试仓库。

---

## 什么是 GitHub Actions？

GitHub Actions 是 GitHub 内置的 CI/CD（持续集成/持续部署）平台，让你可以在仓库中自动化软件工作流。当 Push、PR、创建 Issue 等事件发生时，可以自动触发构建、测试、部署等任务。

核心概念：
- **Workflow（工作流）**：一个可配置的自动化流程，定义在 `.github/workflows/*.yml` 中
- **Job（作业）**：工作流中的一组步骤，默认并行执行
- **Step（步骤）**：Job 中的单个任务（运行命令或使用 Action）
- **Action（动作）**：可复用的单元（可以从 GitHub Marketplace 获取）
- **Runner（运行器）**：执行工作流的服务器（GitHub 托管或自托管）

## 快速开始

1. 在仓库根目录创建 `.github/workflows/` 文件夹
2. 新建一个 `.yml` 文件，例如 `ci.yml`：

```yaml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run a script
        run: echo Hello, world!
```

3. Push 到 GitHub，Actions 会自动运行

## 注意事项

- **Workflow 文件**必须放在 `.github/workflows/` 目录下，格式为 YAML
- **缩进敏感**：YAML 缩进错误会导致工作流解析失败
- **Secret 安全**：敏感信息（Token、密码）使用 `Settings > Secrets and variables > Actions` 存储，通过 `${{ secrets.XXX }}` 引用
- **并发限制**：免费账户有并发 Job 数量和运行时长限制
- **条件执行**：善用 `if` 条件控制步骤执行，避免不必要的资源消耗
- **调试**：可在工作流中添加 `ACTIONS_STEP_DEBUG=true` 开启调试日志
- **本地测试**：可使用 [act](https://github.com/nektos/act) 工具在本地运行 Actions

## 多操作系统构建（Desktop 应用）

**不需要**为每个操作系统单独编写工作流文件。使用 **Matrix 策略（构建矩阵）** 一行配置即可在多个 OS 上并行构建：

```yaml
jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: |
          # 跨平台构建命令
          # 可以使用 runner.os 条件判断不同 OS 的逻辑
```

如果你的 Desktop 应用使用跨平台框架（如 Electron、Qt、Tauri、Flutter 等），一套构建脚本通常可以适配多系统。如果存在平台差异，可以在 Step 中用 `if: runner.os == 'Windows'` 等条件做分支处理，**无需复制整个 workflow**。
