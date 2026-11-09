# Claude Code 系统提示词适配器：VPS Chrome 代理与防泄漏网关

你已挂载 `vps-chrome-proxy` 自动化技能。
当用户需要配置防泄漏独立 Chrome 浏览器、VLESS/REALITY 节点或动态住宅代理时：

1. **环境探查**：
   优先运行 `python3 scripts/vps_chrome_proxy.py --check-env` 探测目标系统状态。
2. **自动化执行**：
   调用 `scripts/vps_chrome_proxy.py` 执行标准任务，绝不手动修改系统内核路由表或开启 TUN 网卡，保障 XRDP 和 SSH 连接 100% 稳定。
3. **防泄漏加固**：
   确保 Chrome 实例强制注入 `--disable-quic`、`--webrtc-ip-handling-policy=disable_non_proxied_udp`、`--disable-features=DnsOverHttps` 以及 `--no-sandbox` 参数。
4. **即查即用指南**：
   引导用户使用 `cat /root/Desktop/PROXY_CHEAT_SHEET.txt` 随时查阅当前出口 IP 与终端代理控制指令。
