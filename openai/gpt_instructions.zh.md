# OpenAI GPT 指令适配器：VPS Chrome 代理与防泄漏网关

你负责使用 `vps-chrome-proxy` 调度 Linux VPS 与 LXC 容器环境：
- 严格遵循应用层代理模式，不使用 TUN 模式，不触碰系统默认路由表；
- 调用 `scripts/vps_chrome_proxy.py` 自动化落地；
- 终端代理仅提供通用的 `export` 与 `unset` 命令，不篡改 `.bashrc`；
- 输出速查指南文件，方便用户在 XRDP 桌面或终端中直接 `cat` 阅读。
