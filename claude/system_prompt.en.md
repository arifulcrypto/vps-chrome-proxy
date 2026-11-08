# Claude Code System Prompt Adapter: VPS Chrome Proxy

You are equipped with the `vps-chrome-proxy` skill.
When the user asks you to configure an isolated Chrome instance, setup a VLESS/REALITY tunnel, or configure residential proxies on a Linux VPS / LXC container:

1. **Verify Target Environment**:
   Run `python3 scripts/vps_chrome_proxy.py --check-env` first.
2. **Execute Provisioning**:
   Use `scripts/vps_chrome_proxy.py` with appropriate parameters instead of typing ad-hoc iptables or route commands.
   - For VLESS links: use `--add-vless "<URL>" --http-port <PORT> --chrome-name "<NAME>"`.
   - Never use TUN mode and never modify the default gateway to avoid dropping SSH or XRDP.
3. **Hardened Chrome Isolation**:
   Always ensure `--disable-quic`, `--force-webrtc-ip-handling-policy=disable_non_proxied_udp`, `--disable-features=DnsOverHttps`, `--no-sandbox`, and `--disable-dev-shm-usage` are passed to Chrome.
4. **Local Cheat Sheet**:
   Remind the user that the setup summary is saved on the target machine and can be inspected via:
   `cat /root/Desktop/PROXY_CHEAT_SHEET.txt`.
