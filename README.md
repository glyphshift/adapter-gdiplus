# Glyphshift GDI+ Adapter

Glyphshift 官方免费基础 Adapter 独立仓库。源码公开，发布产物为双架构 .gsp，可由 Glyphshift 官方安装包按固定版本和摘要预装。

## Adapter ID

- `windows.gdiplus.draw-string`

## 构建

Windows 上执行：

```powershell
./scripts/build.ps1 -Profile Release
```

构建依赖由 sdk.lock.json 固定，不依赖相邻 Glyphshift 主仓 checkout。输出位于 local-test/evidence/packages/。

本仓只拥有具体 Adapter 实现；SDK、Native ABI、Runtime、Controller、安装与 Registry 客户端仍由主仓维护。
