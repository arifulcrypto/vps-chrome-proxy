# Antigravity (AGY) Skill Adapter: VPS Chrome Proxy

This skill is designed for the Google Antigravity Agentic Ecosystem.
It provides high-assurance, leak-proof browser automation and multi-track proxy provisioning for Linux VPS and LXC hosts.

- **Primary Entrypoint**: `scripts/vps_chrome_proxy.py`
- **Configuration Templates**: `templates/`
- **Skill Specification**: `SKILL.md`

## Recommended Workflow:
1. Call `check-env` on target host to inspect architecture, users, and open ports.
2. Call `setup-desktop` if XFCE4, XRDP, or Chrome are missing.
3. Call `setup-vless` or `setup-residential` to spin up background systemd services on dedicated local loopback ports (e.g. 2080, 18080).
4. Call `create-chrome` to produce isolated desktop shortcuts and scripts.
5. Call `test-leak` to guarantee exit IP matches target and no host IP leaks via WebRTC or DNS.
