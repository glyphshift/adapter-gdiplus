# adapter-gdiplus

- 使用中文协作。本仓拥有公开基础 Adapter 源码。
- 依赖固定于 sdk.lock.json，禁止相邻主仓 path 依赖，不修改生成的 .sdk/。
- 使用 scripts/build.ps1 构建、测试和生成 GSP。
- local-test/ 与 lightdeck/ 仅本地使用，不提交。
- 只按稳定 Windows API 泛化，不添加软件标题、安装路径、实机地址或机器信息。
- CI 只验证并上传候选；Registry/Release 发布需显式执行。
