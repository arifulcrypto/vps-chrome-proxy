# VPS Chrome 代理与防泄漏网关引擎

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux%20(Ubuntu%2FDebian)-green.svg)]()
[![Multi-Agent: AGY%20%7C%20Claude%20%7C%20OpenAI](https://img.shields.io/badge/Agents-Antigravity%20%7C%20Claude%20%7C%20OpenAI-purple.svg)]()

> 在 Linux VPS 或 LXC 容器上一键部署防泄漏隔离版 Chrome 浏览器与双轨代理网关（VLESS + 动态住宅代理）。

[English](./README.md) | [中文说明](./README_zh.md)

---

## 🌟 核心特性与架构

`vps-chrome-proxy` 专为追求**生产级桌面环境隔离**、**零路由篡改**以及**严密防范真实 IP 泄露**的开发者与 AI Agent 打造：

### 核心优势：
1. **零断连风险**：不修改系统默认网关（Default Gateway），不安装 TUN 虚拟网卡设备，SSH (22) 与 XRDP (3389) 远程连接 100% 稳定，永不断线。
2. **双轨代理核心架构**：
   - **轨道 A（VLESS + REALITY + Vision）**：原生 Xray 高性能加密隧道，直达美国 NAT（或其它目标落地）。
   - **轨道 B（动态住宅/链式桥接）**：链式转发至按量付费住宅 IP（IPCook、IPRoyal、Smartproxy、Oxylabs），支持桌面一键切地区。
3. **物理级隔离与防泄漏 Chrome**：
   - 彻底封堵 WebRTC STUN 探测；
   - 封死 QUIC (UDP 443) 旁路直连风险；
   - 关闭浏览器本地 DoH，强制由远端节点解析 DNS；
   - 完善适配 root 运行与 XRDP 环境（`--no-sandbox` 与 `--disable-dev-shm-usage`）。
4. **本地速查备忘录生成**：在桌面自动生成格式化说明文档（`PROXY_CHEAT_SHEET.txt`），随时可通过 `cat` 查阅。

---

## 🚀 快速上手

### 1. 基础环境探查
```bash
python3 scripts/vps_chrome_proxy.py --check-env
```

### 2. 本地一键完整部署（VLESS 节点模式）
```bash
python3 scripts/vps_chrome_proxy.py \
  --all-in-one \
  --add-vless "vless://uuid@relay-ip:port?security=reality&encryption=none&pbk=...&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=...&sid=..." \
  --http-port 2080 \
  --socks-port 2081 \
  --chrome-name "US Proxy Chrome"
```

### 3. 远程 SSH 一键部署（针对远程 VPS 或全新 LXC 容器）
```bash
python3 scripts/vps_chrome_proxy.py \
  --ssh-host 192.168.1.100 \
  --ssh-port 22 \
  --ssh-user root \
  --ssh-pass "容器密码" \
  --all-in-one \
  --add-vless "vless://..."
```

---

## 📋 终端按需代理开启与关闭

在当前终端中按需执行通用的 `export` 命令（仅对当前终端生效，不修改 `.bashrc`）：

```bash
# 开启代理
export http_proxy=http://127.0.0.1:2080
export https_proxy=http://127.0.0.1:2080
export all_proxy=http://127.0.0.1:2080

# 验证当前出口 IP
curl https://api.ipify.org

# 关闭代理 (恢复直连)
unset http_proxy https_proxy all_proxy
```

---

## 📖 本地配置备忘录速查

在目标机器上随时执行：
```bash
cat /root/Desktop/PROXY_CHEAT_SHEET.txt
```

---

## 🤖 多 Agent 适配规范

| Agent 平台 | 适配文件位置 | 说明 |
| :--- | :--- | :--- |
| **Antigravity (AGY)** | `SKILL.md`, `.agents/skills/vps-chrome-proxy/` | AGY 标准 Skill 规范定义 |
| **Claude Code** | `claude/system_prompt.en.md` | Claude 提示词适配层 |
| **OpenAI GPTs** | `openai/gpt_instructions.en.md` & `actions_schema.json` | Custom GPT Action 规范 |

---

## 📄 开源许可证

遵循 [MIT License](./LICENSE) 开源协议。
