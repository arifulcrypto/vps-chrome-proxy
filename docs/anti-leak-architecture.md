# Anti-Leak Architecture & Browser Fingerprint Hardening

This document explains why standard proxies frequently leak sensitive real IP addresses and how `vps-chrome-proxy` achieves strict physical and protocol-level leak prevention.

---

## 1. The Three Common Leak Vectors

### Vector A: QUIC / HTTP/3 Proxy Bypass
* **Mechanism**: Chromium browsers aggressively utilize QUIC over UDP port 443. Standard HTTP CONNECT proxies only establish TCP tunnels.
* **The Leak**: When Chrome attempts to connect via QUIC, if the HTTP proxy doesn't handle UDP, Chrome silently falls back to sending UDP packets directly out of the host's default network interface (`eth0`), exposing the server's real datacenter IP (`107.173.10.79`).
* **Our Defense**: `--disable-quic` forces all connections through HTTP/2 or HTTP/1.1 TCP tunnels via the local proxy gateway.

### Vector B: WebRTC STUN / ICE Discovery
* **Mechanism**: WebRTC is designed for peer-to-peer real-time communication. To facilitate NAT traversal, the WebRTC engine sends STUN packets over UDP to discover all available public and private IP addresses.
* **The Leak**: Even with `--proxy-server` enabled, WebRTC by default attempts STUN discovery across all active interfaces. Target websites (OpenAI, Claude, payment processors) execute JavaScript STUN queries to unmask the real server IP.
* **Our Defense**:
  * `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` restricts WebRTC to only use UDP routes that traverse the proxy.
  * `--enforce-webrtc-ip-permission-check` mandates explicit browser permission before binding interfaces.

### Vector C: Local DNS Over HTTPS (DoH) Leak
* **Mechanism**: Chrome features an internal DNS client that can resolve hostnames via built-in secure DNS providers (Google, Cloudflare).
* **The Leak**: If DoH is active, Chrome queries resolvers directly using the host IP before or alongside the proxy request, leaking visited domains and geographic origin.
* **Our Defense**:
  * `--disable-features=DnsOverHttps` disables internal DoH.
  * When using `--proxy-server="http://127.0.0.1:<PORT>"`, Chrome issues `CONNECT hostname:443 HTTP/1.1`, passing the raw hostname directly to the proxy server. All DNS lookups occur strictly on the remote exit node.

---

## 2. Multi-Profile Physical Separation

Running multiple tasks (e.g. GPT subscription, Claude Code login, personal browsing) in a single browser profile leads to session poisoning and tracking cross-contamination:
* **Storage Isolation**: Each instance is assigned an explicit, separate `--user-data-dir` (`/root/.config/chrome-us-proxy`, `/root/.config/chrome-proxy`, etc.).
* **WM_CLASS Isolation**: By assigning `--class="us-proxy-chrome"`, the X11 window manager does not collapse distinct proxy windows into the default Chrome taskbar group.
* **Root Execution Guard**: Adding `--no-sandbox` allows execution under root inside XRDP, while `--disable-dev-shm-usage` prevents shared memory exhaustion.
