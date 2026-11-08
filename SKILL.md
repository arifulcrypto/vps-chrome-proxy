---
name: vps-chrome-proxy
description: >-
  Provisions anti-leak proxy-isolated Chrome browser instances, dual-track
  gateways (VLESS + REALITY + Vision / Dynamic Residential Chains), and remote
  desktop integration on Linux VPS or LXC containers (localhost or over SSH).
---

# VPS Chrome Proxy & Anti-Leak Gateway Engine

> Automated Provisioning Engine for Anti-Leak Proxy-Isolated Chrome Browsers & Multi-Gateway Tunnels on Linux VPS & LXC Instances.

[English](./SKILL.md) | [中文说明](./i18n/SKILL_zh.md)

---

## 1. Overview & Capabilities

`vps-chrome-proxy` is a specialized automation skill designed for AI agents (Antigravity `agy`, Claude Code, OpenAI GPTs) and developers to turn any Linux VPS or LXC container into an isolated, leak-proof browser and terminal development workstation.

### Key Pillars:
- **Zero Route Mutation (Zero Disconnection Risk)**: Does NOT touch system default gateway or install TUN devices. SSH (`22`) and XRDP (`3389`) remain 100% stable and connected.
- **Dual-Track Proxy Architecture**:
  - **Track A (VLESS + REALITY + Vision)**: High-speed, low-latency encrypted tunnel using native Xray, tunneling to dedicated NAT landing nodes (e.g. US Cogent, Singapore, Japan).
  - **Track B (Dynamic Residential Chain Bridge)**: Chain forwarding to residential ISP proxies (IPCook, IPRoyal, Smartproxy, Oxylabs) with on-demand interactive/scripted region switching.
- **Multi-Instance Chrome Physical Isolation**:
  - Independent `--user-data-dir` profiles (e.g., `chrome-us-proxy`, `claude-code-chrome`, `chrome-residential`).
  - Independent desktop `.desktop` entries and `.sh` launchers.
- **Hardened Anti-Leak Flags**:
  - `--disable-quic`: Stops HTTP/3 UDP 443 proxy bypass.
  - `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` & `--enforce-webrtc-ip-permission-check`: Blocks WebRTC STUN requests from exposing host real IP.
  - `--disable-features=DnsOverHttps`: Forces remote DNS resolution via HTTP CONNECT.
  - `--lang=en-US`: Enforces native English browser locale.
  - `--no-sandbox --disable-dev-shm-usage`: Ensures root execution and XRDP desktop stability.
- **On-Demand Terminal Integration**: Non-invasive standard `export` / `unset` commands for Claude Code, Codex, Git, and curl.
- **Local Cheat Sheet Generation**: Auto-creates formatted summary text (`/root/Desktop/PROXY_CHEAT_SHEET.txt`) ready for instant terminal `cat` inspection.

---

## 2. CLI Engine & Agent Invocation

The master automation engine is `scripts/vps_chrome_proxy.py`.

```bash
# Basic Environment Check (Localhost)
python3 scripts/vps_chrome_proxy.py --check-env

# Full All-in-One Deployment (Localhost with VLESS)
python3 scripts/vps_chrome_proxy.py \
  --all-in-one \
  --add-vless "vless://uuid@relay-ip:port?security=reality&encryption=none&pbk=...&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=...&sid=..." \
  --http-port 2080 \
  --socks-port 2081 \
  --chrome-name "US Proxy Chrome"

# Remote Deployment over SSH (e.g., Target LXC Container or Remote VPS)
python3 scripts/vps_chrome_proxy.py \
  --ssh-host 192.168.1.100 \
  --ssh-port 22 \
  --ssh-user root \
  --ssh-pass "SecretPassword" \
  --all-in-one \
  --add-vless "vless://..."
```

---

## 3. Parameter Reference

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--local` | flag | `True` | Run directly on localhost |
| `--ssh-host` | string | `None` | Remote target IP or hostname |
| `--ssh-port` | integer | `22` | Remote target SSH port |
| `--ssh-user` | string | `root` | Target SSH username |
| `--ssh-pass` | string | `None` | Target SSH password |
| `--ssh-key` | string | `None` | Path to SSH private key |
| `--check-env` | flag | - | Run environment and port inspection |
| `--setup-desktop` | flag | - | Install & configure XFCE4, XRDP, and Chrome |
| `--add-vless` | string | `None` | Standard `vless://` URL to parse and deploy |
| `--http-port` | integer | `2080` | Local HTTP proxy inbound port |
| `--socks-port` | integer | `2081` | Local SOCKS5 proxy inbound port |
| `--chrome-name` | string | `US Proxy Chrome` | Display name of Chrome instance |
| `--chrome-profile`| string | `/root/.config/chrome-us-proxy` | Chrome user-data-dir path |
| `--all-in-one` | flag | - | Run complete pipeline, leak tests, and cheat sheet |

---

## 4. Verification & Cheat Sheet

Upon completion, the engine runs automated headless Chrome rendering and curl checks to verify:
1. Native host IP vs Proxy Exit IP;
2. WebRTC non-proxied UDP leakage;
3. Connectivity to OpenAI, Anthropic, and GitHub.

The resulting cheat sheet is saved to `/root/Desktop/PROXY_CHEAT_SHEET.txt` for instant viewing:
```bash
cat /root/Desktop/PROXY_CHEAT_SHEET.txt
```
