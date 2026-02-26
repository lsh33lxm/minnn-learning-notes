---
name: api
description: Generate PowerShell alias functions for Claude Code API platforms. Use when the user wants to add a new API provider shortcut/alias to their PowerShell profile, or mentions adding a new base_url and apikey for Claude Code usage. Triggers on requests like "add a new API alias", "configure a new provider", or "add XX to my profile".
---

# API Alias Generator

## Step 0: Locate Profile File

Do NOT hardcode the profile path. Detect it dynamically:

```bash
powershell.exe -NoProfile -Command "Write-Host $PROFILE"
```

If the file does not exist, create it (including parent directories):

```bash
powershell.exe -NoProfile -Command "New-Item -Path $PROFILE -ItemType File -Force"
```

## Parameter Auto-Detection

User can provide parameters in any order without labels. Auto-detect by format:
- **base_url**: starts with `http://` or `https://`
- **apikey**: starts with `sk-`
- **model**: contains digits, dots, or hyphens, longer than 3 chars (e.g., `qwen3-coder-plus`, `glm-4.7`)
- **alias**: short string (1-5 chars), pure lowercase letters/numbers, none of the above patterns

If ambiguous or missing, use AskUserQuestion to clarify.

When user provides multiple aliases+models with shared url/apikey, batch-create all in one edit.

## Steps

1. Parse user input using auto-detection rules.
2. Run Step 0 to get profile path. Create file if missing.
3. Read the profile file. Check for duplicate `function <alias>`. If duplicate, ask overwrite or rename.
4. Append function block(s) to end of file:

```powershell
function <alias> {
    $env:ANTHROPIC_BASE_URL = "<base_url>"
    $env:ANTHROPIC_AUTH_TOKEN = "<apikey>"
    $env:API_TIMEOUT_MS = "<timeout>"
    $env:CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = "1"
    $env:ANTHROPIC_MODEL = "<model>"
    $env:ANTHROPIC_SMALL_FAST_MODEL = "<model>"
    $env:ANTHROPIC_DEFAULT_SONNET_MODEL = "<model>"
    $env:ANTHROPIC_DEFAULT_OPUS_MODEL = "<model>"
    $env:ANTHROPIC_DEFAULT_HAIKU_MODEL = "<model>"
    claude @args
}
```

Default timeout: `600000`.

5. Show **all** aliases currently in the profile (not just the new one). Parse every `function` block and display a table with platform auto-detected from URL:

Platform detection rules:
- `minimaxi` → MiniMax
- `deepseek` → DeepSeek
- `newcli.com` → Claude
- `dashscope.aliyuncs` → 阿里云
- `openai` → OpenAI
- Otherwise use the domain name

Example output format:

```
| 别名 | 平台    | 模型              |
|------|---------|-------------------|
| mm   | MiniMax | MiniMax-M2.5      |
| ds   | DeepSeek| deepseek-chat     |
| cc   | Claude  | claude-opus-4-6   |
```

6. Remind user: `. $PROFILE`
