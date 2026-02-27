# 求解器安装常见错误排查

## MOSEK 错误

| 错误信息 | 原因 | 解决方法 |
|---|---|---|
| `MEX 文件无效: 找不到指定的模块` | DLL 路径未加入 PATH | startup.m 中 `setenv('PATH',...)` 必须在 `addpath` 之前执行 |
| `mosekopt` 找不到 | MATLAB 路径未配置 | 检查 startup.m，重启 MATLAB |
| 安装路径含空格导致 DLL 加载失败 | Windows DLL 加载器限制 | 重新解压到无空格路径，如 `C:\Users\<用户名>\mosek\` |
| 许可证更新后仍报错 | MATLAB 缓存了旧许可证状态 | 重启 MATLAB |
| `MSK_RES_ERR_IN_ARGUMENT` | 使用了双引号字符串 | 改用单引号：`'string'` 而非 `"string"` |

## Gurobi 错误

| 错误信息 | 原因 | 解决方法 |
|---|---|---|
| `MEX 文件无效: 找不到指定的模块` | DLL 路径未加入 PATH | startup.m 中 `setenv('PATH',...)` 必须在 `addpath` 之前执行 |
| `Error 10009: HostID mismatch` | 许可证绑定了其他机器的 hostid | 在当前机器重新运行 `grbgetkey <KEY>` 申请新许可证 |
| `Error 10009: Unable to open license file` | 许可证文件路径不对 | 确认 `gurobi.lic` 在 `C:\Users\<用户名>\` 或设置 `GRB_LICENSE_FILE` 环境变量 |
| MSI 安装失败 error 1603 | 没有管理员权限 | 用 `-Verb RunAs` 触发 UAC 弹窗，点击"是" |
| `gurobi_setup` 找不到 | MATLAB 路径未配置 | `addpath('C:\gurobi1300\win64\matlab')` |
| `Problem generating unique host ID` | 无稳定网卡 | 临时禁用 VPN 虚拟网卡，保留物理网卡 |

## 许可证文件位置速查

```
MOSEK 许可证：C:\Users\<用户名>\mosek\mosek.lic
Gurobi 许可证：C:\Users\<用户名>\gurobi.lic
```

## 验证环境变量是否生效

```powershell
# PowerShell 查看
[System.Environment]::GetEnvironmentVariable('GUROBI_HOME', 'User')
[System.Environment]::GetEnvironmentVariable('GRB_LICENSE_FILE', 'User')
```

```matlab
% MATLAB 内查看
getenv('GUROBI_HOME')
getenv('GRB_LICENSE_FILE')
getenv('PATH')  % 确认包含 gurobi1300\win64\bin 和 mosek...win64x86\bin
```

## 下载地址格式参考

```
MOSEK: https://download.mosek.com/stable/<版本号>/mosektoolswin64x86.zip
       最新版本查询：https://www.mosek.com/downloads/

Gurobi: https://packages.gurobi.com/<主版本号.0>/Gurobi-<完整版本号>-win64.msi
        示例：https://packages.gurobi.com/13.0/Gurobi-13.0.0-win64.msi
        最新版本查询：https://www.gurobi.com/downloads/gurobi-software/
```
