---
name: matlab-solver-setup
description: 在 Windows 上为 MATLAB 安装并配置 MOSEK 和 Gurobi 优化求解器。包含系统信息检查、下载安装、许可证配置、MATLAB 路径设置和验证测试。当用户需要安装 MOSEK、Gurobi、配置求解器许可证、设置 startup.m、排查 MEX 文件错误或 HostID 不匹配问题时触发。
---

# MATLAB 求解器安装配置（Windows）

## STEP 0：查看本机配置信息

安装前先收集系统信息，避免版本不匹配或权限问题。

```matlab
% MATLAB 命令行运行
ver                     % 查看 MATLAB 版本
version('-release')     % 发行版本号（如 R2023b）
computer('arch')        % 应为 win64
```

```powershell
# PowerShell 运行
# 检查管理员权限（Gurobi MSI 安装必须为 True）
([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# 检查 C 盘剩余空间（需 ≥ 2GB）
Get-PSDrive C | Select-Object Used, Free

# 查看机器 hostid（Gurobi 许可证绑定用）
# 安装 Gurobi 后运行：C:\gurobi1300\win64\bin\grbgetkey.exe --help
# 或查看网卡 MAC 地址
getmac /v /fo list
```

---

## STEP 1：申请许可证

**MOSEK 学术许可证（免费）**
- 申请地址：https://www.mosek.com/products/academic-licenses/
- 用学术邮箱申请，邮件收到 `mosek.lic` 文件

**Gurobi 学术许可证（免费）**
- 注册：https://www.gurobi.com/academia/academic-program-and-licenses/
- 登录 portal.gurobi.com → Licenses → Request License → 复制 UUID 格式的 KEY
- ⚠️ 许可证绑定机器 hostid，必须在目标机器上运行 `grbgetkey`

---

## STEP 2：下载并安装

### MOSEK（zip 方式，无需管理员）

```powershell
# 下载（版本号按实际替换，当前最新 11.1.6）
Start-BitsTransfer -Source "https://download.mosek.com/stable/11.1.6/mosektoolswin64x86.zip" `
    -Destination "C:\Users\<用户名>\solver_install\mosektoolswin64x86.zip"

# 解压（路径不能含空格）
Expand-Archive -Path "C:\Users\<用户名>\solver_install\mosektoolswin64x86.zip" `
    -DestinationPath "C:\Users\<用户名>\mosek" -Force
```

解压后结构：
```
C:\Users\<用户名>\mosek\mosek\11.1\
├── toolbox\R2019b\          ← MATLAB 工具箱
└── tools\platform\win64x86\bin\  ← DLL 目录
```

### Gurobi（MSI 方式，需要管理员 UAC）

```powershell
# 下载（版本号按实际替换，当前最新 13.0.0）
Start-BitsTransfer -Source "https://packages.gurobi.com/13.0/Gurobi-13.0.0-win64.msi" `
    -Destination "C:\Users\<用户名>\solver_install\Gurobi-13.0.0-win64.msi"

# 安装（会弹出 UAC 弹窗，点击"是"）
Start-Process msiexec -ArgumentList '/i "C:\Users\<用户名>\solver_install\Gurobi-13.0.0-win64.msi" /quiet /norestart' -Verb RunAs -Wait
```

默认安装到 `C:\gurobi1300\win64\`

---

## STEP 3：配置许可证

```powershell
# MOSEK：将 mosek.lic 放到用户目录下的 mosek 文件夹
Copy-Item "mosek.lic" "C:\Users\<用户名>\mosek\mosek.lic"

# Gurobi：运行 grbgetkey 自动下载绑定当前机器的许可证（推荐）
"C:\gurobi1300\win64\bin\grbgetkey.exe" <UUID-KEY> --path "C:\Users\<用户名>"
# 自动保存到 C:\Users\<用户名>\gurobi.lic
```

---

## STEP 4：配置环境变量

```powershell
# Gurobi 环境变量（逐条运行）
[System.Environment]::SetEnvironmentVariable('GUROBI_HOME', 'C:\gurobi1300\win64', 'User')
[System.Environment]::SetEnvironmentVariable('GRB_LICENSE_FILE', 'C:\Users\<用户名>\gurobi.lic', 'User')
$p = [System.Environment]::GetEnvironmentVariable('PATH', 'User')
[System.Environment]::SetEnvironmentVariable('PATH', $p + ';C:\gurobi1300\win64\bin', 'User')
```

---

## STEP 5：配置 MATLAB startup.m

创建或编辑 `C:\Users\<用户名>\Documents\MATLAB\startup.m`：

```matlab
% ===== MOSEK 11.1 =====
mosek_bin  = 'C:\Users\<用户名>\mosek\mosek\11.1\tools\platform\win64x86\bin';
mosek_path = 'C:\Users\<用户名>\mosek\mosek\11.1\toolbox\R2019b';
% 关键：setenv 必须在 addpath 之前，否则 MEX 找不到 DLL
if ~contains(getenv('PATH'), 'mosek')
    setenv('PATH', [mosek_bin ';' getenv('PATH')]);
end
if exist(mosek_path, 'dir'), addpath(mosek_path); end
fprintf('[startup] MOSEK 11.1 loaded\n');

% ===== Gurobi 13.0 =====
gurobi_bin  = 'C:\gurobi1300\win64\bin';
gurobi_path = 'C:\gurobi1300\win64\matlab';
if ~contains(getenv('PATH'), 'gurobi1300')
    setenv('PATH', [gurobi_bin ';' getenv('PATH')]);
end
if exist(gurobi_path, 'dir'), addpath(gurobi_path); end
fprintf('[startup] Gurobi 13.0 loaded\n');
```

> 如不想 MOSEK 覆盖 MATLAB 内置的 `linprog`/`quadprog`，将 `R2019b` 改为 `R2019bom`

---

## STEP 6：验证安装

```matlab
% 验证 MOSEK
[r, res] = mosekopt('minimize echo(0)', struct( ...
    'c', [1], 'a', sparse(1,1,1), ...
    'blc', [1], 'buc', [1], 'blx', [0], 'bux', [inf]));
fprintf('MOSEK: %s\n', res.rcodestr);  % 期望: MSK_RES_OK

% 验证 Gurobi
m.obj=[1]; m.A=sparse(1,1,1); m.rhs=[1]; m.sense='='; m.lb=[0];
r = gurobi(m);
fprintf('Gurobi: %s, objval=%g\n', r.status, r.objval);  % 期望: OPTIMAL, 1
```

---

## 常见错误

详见 [references/troubleshooting.md](references/troubleshooting.md)
