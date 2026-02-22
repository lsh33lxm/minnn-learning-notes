# 常见错误排查清单

| 症状 | 原因 | 解决 |
|------|------|------|
| `import torch` 失败 | torch 没装成功 / 环境没激活 | 确认用 `conda run -n <env>` 执行 |
| `cuda.is_available()` 为 False | 装了 CPU 版 / 驱动不可用 | 卸载后用 `--index-url .../cuXXX` 重装 |
| `nvcc not found` | 缺 CUDA Toolkit | 仅编译 CUDA 扩展才需要，pip wheel 不需要 |
| 依赖冲突 | numpy/opencv/protobuf 版本不兼容 | 重建干净环境 + 放宽版本约束 |
| `CUDA out of memory` | smoke test 用了太大 tensor | 减小测试 tensor 尺寸 |
| conda 下载超时 | 网络问题 | 切换镜像通道（Step 2） |
| `ModuleNotFoundError` | 漏装依赖 | 检查 requirements.txt 是否完整安装 |
| `conda run` 报 `--no-banner` 不识别 | conda 版本不支持该参数 | 去掉 `--no-banner` |
| `conda run python -c` 多行报错 | Windows 不支持多行 `-c` 参数 | 写入 .py 文件再执行 |
| `pip install -e .` 报找不到 pyproject | `conda run` 工作目录不对 | 加 `--cwd <repo_path>` |
| conda create 要求接受 TOS | 新版 conda 首次使用 | 执行 `conda tos accept ...` |
| bitsandbytes RuntimeError CUDA Setup | bitsandbytes < 0.43 不支持 Windows | 升级到 >= 0.43.0 |
| bitsandbytes `impl_abstract` AttributeError | bitsandbytes 版本与 torch 不兼容 | 降级 bitsandbytes 到与 torch 兼容的版本 |
| deepspeed 编译失败 | Windows 不支持 | 跳过，训练需在 Linux |
| numpy 被静默升级到 2.x | 其他包拉升了 numpy | 每批安装后检查，回退到 `numpy<2` |
| torch 被替换为 PyPI 版本 | 其他包依赖拉升了 torch | 用 `--index-url` + `--force-reinstall --no-deps` 回退 |
| git+https://...@commit 安装失败 | 浅克隆无法 fetch 指定 commit | 从 requirements.txt 找版本号，装最近正式版 |
| requirements.txt 含内部包报错 | 文件是 pip freeze 导出含私有包 | 改用 pyproject.toml extras 安装 |
