# Proxy Providers & Protocol Integration Guide

`vps-chrome-proxy` supports both dedicated encrypted tunnels (VLESS) and dynamic residential proxy pools.

---

## 1. VLESS + REALITY + Vision Nodes

VLESS with REALITY security and XTLS-Vision flow is the premier anti-censorship and anti-blocking protocol.

### Standard Format:
```text
vless://<UUID>@<RELAY_HOST>:<PORT>?security=reality&encryption=none&pbk=<PUBLIC_KEY>&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=<SNI>&sid=<SHORT_ID>
```

### Automation Logic:
1. `scripts/vps_chrome_proxy.py` parses the URI via standard RFC 3986 URL parsing.
2. Generates an independent Xray client JSON configuration (`/etc/xray-client-us/config.json`).
3. Provisions a dedicated systemd service unit (`xray-client-us.service`).
4. Inbounds are bound exclusively to `127.0.0.1` (`HTTP` port 2080, `SOCKS5` port 2081).
5. Exposes zero public ports to the internet.

---

## 2. Residential Proxy Pools (IPCook, IPRoyal, Smartproxy, Oxylabs)

Residential proxies provide genuine residential ISP IP addresses, ideal for risk-sensitive platforms, anti-fraud algorithms, and payment verification.

### Supported String Format:
```text
HOST:PORT:USER:PASS|Country and Description
# Example:
geo.ipcook.com:32345:sugarsugar-PH:sugarsugar|🇵🇭 Philippines (PH) - PLDT Residential
45.38.107.97:6014:user:pass|🇬🇧 United Kingdom (GB) - London
```

### Region Switcher Script (`switch_proxy.sh`):
The generator writes a interactive and scriptable switching utility on the target Desktop:
```bash
# List all configured regions
/root/Desktop/switch_proxy.sh

# Switch to region #2 (UK)
/root/Desktop/switch_proxy.sh 2
```
It immediately reloads the local `pproxy` gateway listening on `127.0.0.1:18080` without restarting the browser.
