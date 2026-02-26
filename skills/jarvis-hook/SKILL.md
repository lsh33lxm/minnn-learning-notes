---
name: jarvis-hook
description: 为 Claude Code 配置 JARVIS 风格语音通知 Hook 系统。当用户想要设置语音提示、Hook 通知、音频反馈时触发。支持：(1) 配置 Hook 事件（UserPromptSubmit/Stop/Notification/SubagentStop/PreCompact）(2) 使用 edge-tts 生成高质量科幻风语音 (3) 通过 winmm.dll mciSendString 播放 mp3 (4) 可选飞书 webhook 通知。适用于 Windows 环境。
---

# JARVIS Hook - 语音通知系统

为 Claude Code 配置 JARVIS 风格的语音提示，在关键节点自动播放语音通知。

## 架构概览

```
~/.claude/
├── settings.json              ← Hook 事件配置
└── hooks/
    ├── jarvis_hook.py         ← 主 Hook 脚本（Python + ctypes 直调 winmm.dll）
    ├── generate_sounds.py     ← 语音生成工具（edge-tts 神经网络语音）
    └── sounds/
        └── *.mp3              ← 生成的语音文件
```

## 支持的 Hook 事件

| 事件 | 触发时机 | 默认语音 |
|------|---------|---------|
| `UserPromptSubmit` | 用户发送指令 | "System online. At your service." |
| `Notification` (permission_prompt) | Claude 需要确认权限 | "Awaiting confirmation." |
| `Stop` | 主任务完成 | "Mission accomplished." |
| `SubagentStop` | 子代理完成 | "Sub-agent protocol complete." |
| `PreCompact` | 上下文压缩前 | "Initiating context compression." |

## 工作流程

### Step 1: 安装 edge-tts

```bash
py -3 -m pip install edge-tts
```

### Step 2: 创建 hooks 目录和脚本

将 `scripts/jarvis_hook.py` 复制到 `~/.claude/hooks/jarvis_hook.py`。
将 `scripts/generate_sounds.py` 复制到 `~/.claude/hooks/generate_sounds.py`。

### Step 3: 自定义语音参数

编辑 `generate_sounds.py` 中的配置：

- `VOICE`: 声线选择（推荐科幻风用 `en-US-EricNeural`）
- `PITCH`: 音调偏移（如 `-10Hz` 降低音调增加机械感）
- `RATE`: 语速（如 `+12%` 加速）
- `MESSAGES`: 各事件对应的语音台词

可选声线参考：

| 声线 | 风格 | 适合场景 |
|------|------|---------|
| `en-US-EricNeural` | Rational 冷静理性 | 机械科幻 AI |
| `en-US-ChristopherNeural` | Authority 权威 | 指挥官风 |
| `en-GB-RyanNeural` | Friendly 友好 | 经典 JARVIS |
| `en-US-SteffanNeural` | Rational 理性 | 冷峻分析师 |

### Step 4: 生成语音文件

```bash
py -3 ~/.claude/hooks/generate_sounds.py
```

### Step 5: 配置 settings.json

在 `~/.claude/settings.json` 的 `hooks` 字段中添加事件配置。每个事件指向同一个 `jarvis_hook.py` 脚本，脚本内部根据 `hook_event_name` 路由到对应音频。

配置模板：

```json
{
  "hooks": {
    "<EventName>": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "py -3 C:/Users/<USERNAME>/.claude/hooks/jarvis_hook.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

将 `<EventName>` 替换为需要的事件名，`<USERNAME>` 替换为实际用户名。

### Step 6: 重启 Claude Code

Hooks 在会话启动时加载，修改后需重启生效。

## 关键技术点

### Windows 音频播放

使用 Python `ctypes` 直接调用 `winmm.dll` 的 `mciSendStringW` API。避免使用 PowerShell（启动慢）或 `WMPlayer.OCX` COM 对象（非交互式进程中无法输出音频）。

### 性能优化

Python + ctypes 方案比 PowerShell 方案快的原因：
- 省去 PowerShell 冷启动开销（~500ms）
- 省去 C# `Add-Type` 编译开销（~200ms）
- ctypes 直接调用 DLL，零中间层

### Stop 事件防死循环

Stop hook 必须检查 `stop_hook_active` 字段，为 `true` 时直接 exit 0，否则会无限触发。

### Hook stdin JSON 格式

所有 Hook 通过 stdin 接收 JSON，包含 `hook_event_name` 和事件特定字段。脚本必须输出有效 JSON 并以 exit code 0 退出。

## 扩展：飞书通知

在 `jarvis_hook.py` 的 Stop 事件分支中添加飞书 webhook 调用：

```python
import urllib.request
webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/<YOUR_TOKEN>"
body = json.dumps({"msg_type": "text", "content": {"text": "Claude Code task completed"}}).encode()
req = urllib.request.Request(webhook, data=body, headers={"Content-Type": "application/json"})
urllib.request.urlopen(req)
```
