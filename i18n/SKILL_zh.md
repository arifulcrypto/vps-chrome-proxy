---
name: vps-chrome-proxy
description: >-
  在 Linux VPS 或 LXC 容器（本地或通过 SSH）上一键部署防泄漏代理隔离版 Chrome 浏览器、
  双轨网关隧道（VLESS+REALITY+Vision / 动态住宅代理链）与远程桌面集成。
---

# VPS Chrome 代理与防泄漏网关引擎 (Skill)

> 专为 AI Agent 与开发者设计的自动化运维技能：构建防泄漏独立 Chrome 实例与多轨代理网关。

[English](../SKILL.md) | [中文说明](./SKILL_zh.md)

---

## 1. 核心特性与架构

`vps-chrome-proxy` 能够将任意 Linux VPS 或 LXC 容器（如通过 `vps-lxc-creator` 批量孵化的容器）快速打造成高安全隔离级别的桌面与终端开发工作站：

- **零路由篡改（零断连风险）**：不使用 TUN 虚拟网卡，不修改系统默认路由表（Default Gateway），SSH (22) 与 XRDP (3389) 连接 100% 稳定，绝不掉线。
- **双轨代理核心架构**：
  - **轨道 A（VLESS + REALITY + Vision）**：基于原生 Xray 26.9.9 构建的高性能隧道，直达美国 NAT 落地（或其他指定节点）。
  - **轨道 B（动态住宅/链式桥接）**：通过轻量 `pproxy` 桥接按量付费住宅 IP（IPCook、IPRoyal、Smartproxy、Oxylabs），支持桌面一键切地区。
- **Chrome 多实例物理级隔离**：
  - 独立 `--user-data-dir` 目录，彻底物理隔离 Cookie、LocalStorage 和指纹；
  - 独立 `.desktop` 桌面图标与启动脚本。
- **全方位防泄漏参数加固**：
  - `--disable-quic`：封锁 UDP 443 旁路直连，杜绝代理绕过；
  - `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` 与 `--enforce-webrtc-ip-permission-check`：彻底封堵 WebRTC STUN 泄露真实本机 IP；
  - `--disable-features=DnsOverHttps`：关闭本地 DoH，强制由远端节点解析 DNS；
  - `--lang=en-US`：原生英文界面与环境；
  - `--no-sandbox --disable-dev-shm-usage`：适配 root 身份及 XRDP 渲染环境。
- **终端按需即开即用**：标准 `export` / `unset` 指令，非侵入式设计，不篡改 `.bashrc`。
- **本地速查备忘录生成**：在桌面自动生成格式化说明文档（`PROXY_CHEAT_SHEET.txt`），随时可通过 `cat` 命令即查即用。

---

## 2. 自动化调用示例

执行核心调度脚本：`scripts/vps_chrome_proxy.py`。

```bash
# 本机环境检测
python3 scripts/vps_chrome_proxy.py --check-env

# 一键完整部署 (本地部署 VLESS 节点)
python3 scripts/vps_chrome_proxy.py \
  --all-in-one \
  --add-vless "vless://uuid@relay-ip:port?security=reality&encryption=none&pbk=...&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=...&sid=..." \
  --http-port 2080 \
  --socks-port 2081 \
  --chrome-name "US Proxy Chrome"

# 远程 SSH 自动化部署 (针对全新 LXC 容器或异地 VPS)
python3 scripts/vps_chrome_proxy.py \
  --ssh-host 192.168.1.100 \
  --ssh-port 22 \
  --ssh-user root \
  --ssh-pass "容器密码" \
  --all-in-one \
  --add-vless "vless://..."
```

---

## 3. 本地指南速查 (cat)

部署完成后，目标桌面自动生成备忘录文件：
```bash
cat /root/Desktop/PROXY_CHEAT_SHEET.txt
```
文件包含：
* 原生机房 IP vs 当前代理实际出口 IP
* 终端开启代理命令（`export http_proxy=...`）与关闭代理命令（`unset ...`）
* 各个 Chrome 独立实例与桌面图标对应表
* systemd 服务管理与日志排查指令
