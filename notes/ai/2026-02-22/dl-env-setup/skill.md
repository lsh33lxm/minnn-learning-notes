---
name: dl-env-setup
description: "Automatically configure deep learning environments (Conda + PyTorch/TensorFlow/JAX + CUDA) for any research repo. Use this skill when the user wants to: set up a deep learning or ML training/inference environment, reproduce a paper's code or configure a research repo's runtime, install PyTorch (or TensorFlow/JAX) with GPU/CUDA support, troubleshoot PyTorch + CUDA environment issues, or create a conda/venv environment for any DL project. Do NOT trigger for: general Python project setup without DL frameworks, pure data science (pandas/sklearn) without GPU needs, or frontend/web/non-ML projects."
---

# 自动配置深度学习环境（Conda + PyTorch + CUDA）

## 目标

对任意"论文/项目代码仓库"（训练/推理/复现）自动完成：
1. 创建隔离环境（优先 conda/mamba，其次 venv）
2. 安装匹配的 PyTorch（CPU 或 GPU，自动推断 CUDA 版本）
3. 安装项目依赖（requirements / pyproject / environment.yml）
4. 如需编译 CUDA 扩展则完成编译或给出可执行替代方案
5. 运行最小验证（smoke test），产出可复现锁定文件与日志

---

## 输入（可选参数）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| repo_path | 当前目录 | 本地仓库路径（已 clone） |
| repo_url | — | 仓库地址（若 repo_path 不存在则 clone） |
| mode | 自动检测 | `gpu` / `cpu` |
| python_version | 3.10 | 若项目声明则遵从 |
| env_manager | 自动选择 | `conda` / `mamba` / `micromamba` / `venv`（优先 micromamba > conda > venv） |
| torch_cuda | 自动推断 | 如 `cu118` / `cu121` / `cu124`（GPU 模式） |
| dl_framework | pytorch | `pytorch` / `tensorflow` / `jax`（根据项目依赖自动判断） |
| mirrors | 自动选择 | conda_channel / pip_index（根据网络环境决定） |
| extras | — | `notebooks` / `dev` / `train` / `demo`（若项目支持 `.[extra]`） |

---

## 输出（交付物）

必须产出：
- `verify_env.py`：环境验证脚本（导入关键包 + CUDA 检测 + 小 tensor 运算）
- `install.log`：完整安装日志

可选产出（用户要求时生成）：
- `requirements.lock.txt`：pip freeze 锁定
- `environment.lock.yml`：conda env export --from-history（若使用 conda）
- `smoke_test.sh`：一键验证脚本

---

## 安全与边界

- 不运行长时间训练；只做秒/分钟级 smoke test
- 不读取/上传仓库中的私密数据
- GPU 工具链缺失时，优先提供 CPU 可运行方案 + 明确提示缺什么
- 不修改系统级 conda/pip 配置（镜像通过命令行参数临时指定）

---

## 平台检测与适配（实战经验）

### 平台判断
```bash
# 判断操作系统
uname -s 2>/dev/null  # Linux / Darwin / MINGW64_NT-*(Windows Git Bash)
```

记录变量：`platform` = linux / windows / macos

### Windows 平台关键限制

**1. `conda run` 注意事项：**
- `--no-banner` 在部分 conda 版本不支持，不要使用
- **多行 `python -c "..."` 在 Windows 上会报错**，必须将代码写入 `.py` 文件再执行
- 必须加 `--cwd <repo_path>` 指定工作目录（Claude Code 默认在 system32）

**2. Windows 不兼容包清单（遇到时自动跳过，不要等安装失败）：**

| 包 | Windows 状态 | 替代方案 |
|---|---|---|
| deepspeed | 不支持 | 跳过，训练需在 Linux |
| flash-attn | 不支持（需 Linux + nvcc 编译） | 跳过，模型会自动回退到标准 attention |
| triton | 不支持 | 跳过 |
| bitsandbytes < 0.43.0 | 不支持 | 升级到 >= 0.43.0 |
| bitsandbytes >= 0.44.0 | 可能需要更新 torch | 需检查与项目 torch 版本的兼容性 |

**3. 路径与命令差异：**
- 使用 `/c/Users/...` 风格路径（Git Bash）
- `$HOME` / `$USERPROFILE` 可能为空，用绝对路径
- 不要用 `tee`（部分场景不可用），用 `> file 2>&1` 重定向

### conda run 统一用法（跨平台）

```bash
# 标准格式（不加 --no-banner，加 --cwd）
conda run -n <env_name> --cwd <repo_path> pip install <pkg>
conda run -n <env_name> --cwd <repo_path> python verify_env.py

# Linux 也可用方案 B：直接调用环境内可执行文件
CONDA_PREFIX=$(conda info --envs | grep <env_name> | awk '{print $NF}')
$CONDA_PREFIX/bin/pip install torch

# venv 场景：同一命令链
source /path/to/venv/bin/activate && pip install torch
```

**整个 skill 中所有 pip/python 命令都必须遵守此规则。**
**所有验证代码必须写入 .py 文件执行，禁止依赖多行 `python -c`。**

---

## Step 0：仓库探测（Repo Discovery）

1. 确保仓库存在（必要时 `git clone`）
2. 探测依赖清单（按优先级扫描）：
   - `environment.yml` / `environment.yaml`
   - `pyproject.toml` / `poetry.lock`
   - `requirements.txt` / `requirements/*.txt` / `constraints.txt`
   - `setup.py` / `setup.cfg`
   - `INSTALL.md` / `README.md` / `docs/installation*`
3. 自动判断 `dl_framework`：
   - 依赖中含 `torch` / `torchvision` -> pytorch
   - 依赖中含 `tensorflow` / `tf-*` -> tensorflow
   - 依赖中含 `jax` / `jaxlib` -> jax
   - 均无 -> 默认 pytorch
4. 解析项目要求的 Python 版本；无声明则用 3.10
5. **判断 requirements.txt 质量**（实战经验：很多项目的 requirements.txt 是 pip freeze 导出）：
   - 行数 > 100 -> 大概率是 freeze dump
   - 包含非公开包名（如 `byted-*`、`internal-*`、公司内部包） -> 不能直接用
   - 同时存在 pyproject.toml 的 extras -> 优先用 extras，requirements.txt 仅作版本参考
   - 标记变量：`req_txt_quality` = `clean` / `freeze_dump` / `has_private_pkgs`

记录变量：
- `detected_manifests`：找到的依赖文件列表
- `declared_python`：项目声明的 Python 版本
- `detected_extras`：可用的 extras
- `dl_framework`：推断的框架
- `req_txt_quality`：requirements.txt 质量评估

---

## Step 1：硬件与系统检测

### 1.1 GPU 检测
```bash
# 检测 NVIDIA GPU
nvidia-smi --query-gpu=driver_version,name,memory.total --format=csv,noheader 2>/dev/null
```
- 有输出 -> `mode=gpu`，记录 Driver Version
- 无输出 / 命令不存在 -> `mode=cpu`

### 1.2 CUDA 版本自动推断（GPU 模式）
```bash
# 从 nvidia-smi 获取 Driver 支持的最高 CUDA 版本
nvidia-smi | grep "CUDA Version" | awk '{print $9}'
```

推断 `torch_cuda` 的逻辑：
1. 取 nvidia-smi 报告的 CUDA Version（如 12.8）
2. 映射到 PyTorch 支持的最近 wheel 标签：
   - CUDA 12.8+ -> `cu128`（若 PyTorch 已发布）否则 `cu124`
   - CUDA 12.1~12.7 -> `cu121`
   - CUDA 11.8~11.x -> `cu118`
   - CUDA < 11.8 -> 警告驱动过旧，建议升级，回退 `cpu`
3. 若项目明确指定了 CUDA 版本，以项目为准

### 1.3 补充规则
- Driver Version >= CUDA Runtime Version 才能运行
- PyTorch 的 pip wheel 自带 CUDA runtime，多数情况无需单独装 CUDA Toolkit
- 仅"需要编译 CUDA 扩展"的项目才强依赖 `nvcc`

记录变量：
- `mode`：gpu / cpu
- `driver_version`
- `cuda_version`（Driver 支持的最高版本）
- `torch_cuda`：推断的 wheel 标签（如 cu121）

---

## Step 2：镜像与通道策略

### 2.1 网络环境检测
```bash
# 测试 PyPI 官方源延迟
timeout 5 curl -s -o /dev/null -w "%{time_total}" https://pypi.org/simple/ 2>/dev/null || echo "timeout"
```
- 延迟 < 2s -> 使用官方源
- 延迟 >= 2s 或超时 -> 使用国内镜像

### 2.2 Conda 镜像（临时指定，不改全局配置）
```bash
# 通过 -c 参数临时指定，不修改 ~/.condarc
conda create -n <env> python=3.10 -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main -y
```

可选镜像：
- 清华：`https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main`
- 北外：`https://mirrors.bfsu.edu.cn/anaconda/pkgs/main`
- 阿里：`http://mirrors.aliyun.com/anaconda/pkgs/main`

### 2.3 Pip 镜像
```bash
# 通过 -i 临时指定（注意：pip 的 -c 是 constraints 文件，不是镜像）
pip install <pkg> -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**PyTorch 安装始终使用官方 index-url**（`https://download.pytorch.org/whl/cuXXX`），不走国内 pip 镜像。

记录变量：
- `use_mirror`：true / false
- `conda_channel`
- `pip_index`

---

## Step 3：创建虚拟环境

### 3.0 前置检查：conda/Python 是否存在（实战经验）

若 conda/mamba/micromamba/python 均不存在，需先安装：

```bash
# 检测
micromamba --version 2>/dev/null || mamba --version 2>/dev/null || conda --version 2>/dev/null || python --version 2>/dev/null
```

若全部不存在 -> 询问用户选择安装方式：
- **Miniconda**（推荐）：轻量，自带 Python
- **Miniforge**：社区版，默认 conda-forge

安装流程（以 Miniconda 为例）：
```bash
# Linux
curl -LO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3

# Windows（静默安装）
curl -LO https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
start //wait <installer>.exe /InstallationType=JustMe /RegisterPython=1 /AddToPath=1 /S /D=C:\Users\<user>\miniconda3
```

**安装后必须处理 conda TOS（新版 conda 要求）：**
```bash
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/msys2  # Windows only
```

### 3.1 检测可用的环境管理器
```bash
# 按优先级检测
micromamba --version 2>/dev/null || mamba --version 2>/dev/null || conda --version 2>/dev/null || python -m venv --help >/dev/null 2>&1
```

### 3.2 环境命名
格式：`dl_<项目名>_py<版本>`，如 `dl_yolov8_py310`

### 3.3 创建环境
```bash
# Conda/Mamba
conda create -n <env_name> python=<python_version> -y [-c <conda_channel>]

# 或 venv
python -m venv /path/to/<env_name>
```

### 3.4 检查已有环境（避免冲突）
```bash
conda env list | grep <env_name>
```
若已存在，询问用户：复用 / 删除重建 / 换名

记录变量：
- `env_manager`：实际使用的管理器
- `env_name`
- `python_version`

---

## Step 4：安装 DL 框架

### 4.1 PyTorch（dl_framework=pytorch）

**GPU 模式：**
```bash
conda run -n <env_name> --no-banner pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/<torch_cuda>
# 示例：--index-url https://download.pytorch.org/whl/cu121
```

**CPU 模式：**
```bash
conda run -n <env_name> --no-banner pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

说明：
- `torchvision`：图像相关项目必装
- `torchaudio`：音频相关项目才装，否则可省略
- 始终使用 PyTorch 官方 index-url，不走国内 pip 镜像
- Windows 平台：先检查"Windows 不兼容包清单"，跳过不支持的包

### 4.4 版本钉死与防篡改策略（实战经验）

**问题：** pip 安装后续包时会静默升级 numpy/torch 等关键包，导致环境崩溃。

**安装 PyTorch 后立即钉死 numpy：**
```bash
conda run -n <env_name> pip install torch==X.X.X ... --index-url ...
conda run -n <env_name> pip install "numpy<2"  # torch 2.x 系列需要 numpy<2
```

**每批依赖安装后执行版本一致性检查：**
```bash
# 写入 _check_versions.py 文件执行（不要用 python -c）
conda run -n <env_name> --cwd <repo_path> python _check_versions.py
```

`_check_versions.py` 内容：
```python
import torch
assert "cu" in torch.__version__ or "cpu" in torch.__version__, f"torch 被替换为 PyPI 版本: {torch.__version__}"
import numpy; assert int(numpy.__version__.split('.')[0]) < 2, f"numpy 被升级到 2.x: {numpy.__version__}"
print("Version check OK")
```

**若版本被篡改，立即回退：**
```bash
conda run -n <env_name> pip install torch==X.X.X --index-url https://download.pytorch.org/whl/<torch_cuda> --force-reinstall --no-deps
conda run -n <env_name> pip install "numpy<2"
```

### 4.2 TensorFlow（dl_framework=tensorflow）
```bash
# GPU 版（TF 2.x 自动检测 GPU）
conda run -n <env_name> --no-banner pip install tensorflow
# CPU 版
conda run -n <env_name> --no-banner pip install tensorflow-cpu
```

### 4.3 JAX（dl_framework=jax）
```bash
# GPU 版
conda run -n <env_name> --no-banner pip install "jax[cuda12]"
# CPU 版
conda run -n <env_name> --no-banner pip install jax
```

---

## Step 5：验证框架安装（必须闭环）

**重要：所有验证代码必须写入 .py 文件执行，不要用多行 `python -c`（Windows 不支持）。**

### 5.1 生成框架验证脚本 `_verify_framework.py`

根据 `dl_framework` 生成对应内容，写入文件后执行：

```python
# PyTorch 版本
import torch
print('torch:', torch.__version__)
print('cuda_available:', torch.cuda.is_available())
print('cuda_version:', torch.version.cuda)
if torch.cuda.is_available():
    print('gpu_name:', torch.cuda.get_device_name(0))
    x = torch.randn(2,3).cuda()
    print('gpu_tensor_ok:', x.device)
```

执行方式：
```bash
conda run -n <env_name> --cwd <repo_path> python _verify_framework.py
```

### 5.2 GPU 模式下验证失败的排查
若 `torch.cuda.is_available() == False`（或 TF/JAX 无 GPU）：
1. 确认 `nvidia-smi` 正常输出
2. 检查是否误装了 CPU 版 -> 卸载后重装 GPU 版
3. 检查 `torch_cuda` 版本是否与 Driver 兼容
4. 重装命令加 `--force-reinstall`

---

## Step 6：安装项目依赖

### 6.0 requirements.txt 质量预处理（实战经验）

根据 Step 0 的 `req_txt_quality` 判断：

**若 `freeze_dump` 或 `has_private_pkgs`：**
- 不直接 `pip install -r requirements.txt`
- 优先用 pyproject.toml 的 extras（如 `pip install -e ".[train]"`）
- 仅将 requirements.txt 作为版本参考（查看项目实际用了哪些版本）

**若 `clean`：**
- 可直接使用 `pip install -r requirements.txt`

### 6.1 优先级策略

按以下顺序处理（不互斥，可能需要组合）：

**情况 A：有 environment.yml**
```bash
# 先用 conda 装 yml 中的依赖
conda env update -n <env_name> -f environment.yml
# 再检查是否还有 requirements.txt 需要补装（yml 可能不含所有 pip 包）
if [ -f requirements.txt ]; then
    conda run -n <env_name> --no-banner pip install -r requirements.txt
fi
```

**情况 B：有 requirements.txt（无 environment.yml）**
```bash
conda run -n <env_name> --no-banner pip install -r requirements.txt [-i <pip_index>]
```

**情况 C：Python 包项目（setup.py / pyproject.toml）**
```bash
conda run -n <env_name> --no-banner pip install -e . [-i <pip_index>]
# 需要 extras 时：
conda run -n <env_name> --no-banner pip install -e ".[notebooks,dev]"
```

### 6.2 依赖冲突处理
- 若 `pip install -r requirements.txt` 失败，尝试去掉严格版本锁定（`==` -> `>=`）
- 常见冲突源：`numpy`、`opencv-python`、`protobuf` 版本与 torch 不兼容
- 冲突无法自动解决时，向用户报告具体冲突并建议手动调整

### 6.3 git 依赖安装失败的回退策略（实战经验）

pyproject.toml 中常见 `pkg@git+https://...@<commit_hash>` 格式的依赖。

**失败原因：** 浅克隆无法 fetch 到指定 commit / 仓库已删除 / 网络问题

**回退流程：**
1. 从 requirements.txt 中查找该包的实际版本号（如 `transformers==4.40.0.dev0`）
2. 安装最接近的正式发布版（如 `transformers==4.40.0`）
3. 向用户说明替代情况及可能的兼容性风险

### 6.4 Windows 平台：跳过不兼容包（实战经验）

安装前先过滤 Windows 不兼容的包（参见"平台检测与适配"章节的清单）：
- `deepspeed` -> 跳过
- `flash-attn` -> 跳过
- `triton` -> 跳过
- `bitsandbytes` -> 若项目指定 < 0.43.0，升级到 0.43.0（首个 Windows 版本），但需检查与项目 torch 版本的兼容性

### 6.5 每批安装后执行版本一致性检查

每安装一批依赖后，运行 `_check_versions.py`（见 Step 4.4）确认 torch/numpy 未被篡改。若被篡改则立即回退修复。

---

## Step 7：CUDA 扩展编译（可选）

### 7.1 检测是否需要编译
扫描以下信号：
- `setup.py` 含 `CUDAExtension` / `torch.utils.cpp_extension`
- `README` / `INSTALL` 提到 `nvcc` / `CUDA toolkit` / `build from source`
- 存在 `.cu` / `.cuh` 文件

### 7.2 编译流程
```bash
# 检查 nvcc 是否可用
conda run -n <env_name> --no-banner nvcc --version 2>/dev/null

# 若可用，尝试编译
conda run -n <env_name> --no-banner pip install -e . 2>&1 | tee -a install.log
```

### 7.3 nvcc 缺失时的处理
优先级：
1. 检查项目是否支持跳过编译（如 `SKIP_CUDA_BUILD=1`、`NO_CUDA=1`）
2. 检查是否有预编译 wheel 可用
3. 若都不行 -> 明确提示用户：
   ```
   需要安装 CUDA Toolkit（版本需匹配 torch.version.cuda = <cuda_version>）
   下载地址：https://developer.nvidia.com/cuda-toolkit-archive
   ```
4. 同时提供 CPU 回退方案（如果项目支持）

---

## Step 8：Smoke Test

### 8.1 生成 verify_env.py
```python
#!/usr/bin/env python3
"""环境验证脚本 - 自动生成"""
import sys

def check():
    errors = []

    # 基础导入
    try:
        import torch
        print(f"torch: {torch.__version__}")
        print(f"cuda_available: {torch.cuda.is_available()}")
        print(f"cuda_version: {torch.version.cuda}")
        if torch.cuda.is_available():
            x = torch.randn(2, 3).cuda()
            print(f"gpu_tensor: {x.device} OK")
    except Exception as e:
        errors.append(f"torch: {e}")

    # 项目核心依赖（根据 Step 0 探测结果动态填充）
    for pkg in [<detected_core_packages>]:
        try:
            __import__(pkg)
            print(f"{pkg}: OK")
        except ImportError as e:
            errors.append(f"{pkg}: {e}")

    if errors:
        print(f"\nFAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\nAll checks passed.")

if __name__ == "__main__":
    check()
```

### 8.2 运行验证
```bash
conda run -n <env_name> --no-banner python verify_env.py 2>&1 | tee -a install.log
```

### 8.3 可选：项目级 demo
- 若仓库有 `demo/` / `inference.py` / `predict.py`，用最小输入跑一次
- 仅在明确轻量时运行，不跑完整训练
- `pytest` 仅在项目测试明确很轻量时才运行

### 8.4 生成 smoke_test.sh
```bash
#!/bin/bash
set -e
echo "=== DL Environment Smoke Test ==="
conda run -n <env_name> --no-banner python verify_env.py
echo "=== Smoke test passed ==="
```

---

## Step 9：可复现导出

```bash
# 必须：pip freeze 锁定
conda run -n <env_name> --no-banner pip freeze > requirements.lock.txt

# 可选：conda 导出（用户要求时）
conda env export -n <env_name> --from-history > environment.lock.yml
```

最终交付文件清单：
- `verify_env.py` - 环境验证脚本
- `install.log` - 安装日志
- `smoke_test.sh` - 一键验证（可选）
- `requirements.lock.txt` - pip 锁定（可选）
- `environment.lock.yml` - conda 锁定（可选）

---

## 常见错误排查

遇到安装或运行问题时，查阅 [references/troubleshooting.md](references/troubleshooting.md)（18 条实战经验，覆盖 Windows 兼容性、版本篡改、依赖冲突等）。

---

## 完成条件（Completion Criteria）

全部满足才算完成：
1. `python verify_env.py` 成功退出（exit code 0）
2. GPU 模式下 `torch.cuda.is_available() == True`（或对应框架的 GPU 检测通过）
3. 项目核心 import 全部成功
4. 至少一个最小 demo/入口可运行（如项目提供）
5. `verify_env.py` 和 `install.log` 已生成

若无法全部满足，向用户明确报告：
- 哪些条件已满足
- 哪些条件未满足及原因
- 建议的下一步操作
