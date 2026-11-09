#!/usr/bin/env python3
"""
================================================================================
VPS Chrome Proxy Engine (vps-chrome-proxy)
================================================================================
Automated deployment of anti-leak proxy-isolated Chrome instances, dual-track
gateways (VLESS + REALITY / Residential), and desktop integration for Linux VPS
and LXC containers (Localhost or over SSH).

Author: arifulcrypto
License: MIT
================================================================================
"""

import argparse
import json
import logging
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("vps-chrome-proxy")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = PROJECT_DIR / "templates"


class TargetExecutor:
    """Handles command execution and file operations on Localhost or Remote SSH."""

    def __init__(
        self,
        is_local=True,
        host="127.0.0.1",
        port=22,
        user="root",
        password=None,
        key_file=None,
    ):
        self.is_local = is_local
        self.host = host
        self.port = int(port)
        self.user = user
        self.password = password
        self.key_file = key_file
        self.ssh_client = None

        if not self.is_local:
            self._init_ssh()

    def _init_ssh(self):
        try:
            import paramiko

            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.user,
                "timeout": 15,
            }
            if self.key_file and os.path.exists(self.key_file):
                kwargs["key_filename"] = self.key_file
            elif self.password:
                kwargs["password"] = self.password
            self.ssh_client.connect(**kwargs)
            logger.info(f"Connected to remote host {self.user}@{self.host}:{self.port} via SSH.")
        except ImportError:
            logger.warning(
                "Paramiko library not installed. Falling back to native system ssh command."
            )
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}:{self.port} via SSH: {e}")
            raise

    def run(self, cmd, check=True, capture=True):
        """Execute a shell command either locally or remotely."""
        if self.is_local:
            res = subprocess.run(
                cmd,
                shell=True,
                executable="/bin/bash",
                text=True,
                capture_output=capture,
            )
            if check and res.returncode != 0:
                logger.error(f"Command failed (code {res.returncode}): {cmd}\nStderr: {res.stderr}")
                raise subprocess.CalledProcessError(res.returncode, cmd, res.stdout, res.stderr)
            return res.stdout.strip() if capture else ""
        else:
            if self.ssh_client:
                stdin, stdout, stderr = self.ssh_client.exec_command(f"/bin/bash -c {json.dumps(cmd)}")
                exit_code = stdout.channel.recv_exit_status()
                out_str = stdout.read().decode("utf-8").strip()
                err_str = stderr.read().decode("utf-8").strip()
                if check and exit_code != 0:
                    logger.error(f"Remote command failed (code {exit_code}): {cmd}\nStderr: {err_str}")
                    raise RuntimeError(f"Remote command failed: {cmd}\n{err_str}")
                return out_str
            else:
                # Fallback to system ssh command
                ssh_cmd = ["ssh", "-p", str(self.port), f"{self.user}@{self.host}", cmd]
                res = subprocess.run(ssh_cmd, text=True, capture_output=capture)
                if check and res.returncode != 0:
                    logger.error(f"SSH command failed: {cmd}\nStderr: {res.stderr}")
                    raise subprocess.CalledProcessError(res.returncode, ssh_cmd, res.stdout, res.stderr)
                return res.stdout.strip() if capture else ""

    def write_file(self, remote_path, content, mode="0644"):
        """Write content to a file on local or remote host."""
        if self.is_local:
            p = Path(remote_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            subprocess.run(f"chmod {mode} {remote_path}", shell=True)
        else:
            if self.ssh_client:
                sftp = self.ssh_client.open_sftp()
                # Ensure remote dir
                remote_dir = str(Path(remote_path).parent)
                self.run(f"mkdir -p {remote_dir}")
                with sftp.file(remote_path, "w") as f:
                    f.write(content)
                sftp.chmod(remote_path, int(mode, 8))
                sftp.close()
            else:
                escaped = content.replace("'", "'\\''")
                self.run(f"mkdir -p $(dirname {remote_path}) && echo '{escaped}' > {remote_path} && chmod {mode} {remote_path}")

    def file_exists(self, remote_path):
        cmd = f"[ -f {remote_path} ] && echo 1 || echo 0"
        return self.run(cmd).strip() == "1"

    def command_exists(self, cmd_name):
        cmd = f"which {cmd_name} >/dev/null 2>&1 && echo 1 || echo 0"
        return self.run(cmd).strip() == "1"


def parse_vless_url(vless_url: str) -> dict:
    """Parse standard VLESS REALITY URL into configuration dictionary."""
    if not vless_url.startswith("vless://"):
        raise ValueError("Invalid VLESS URL scheme. Must start with 'vless://'")

    parsed = urlparse(vless_url)
    uuid = parsed.username
    host = parsed.hostname
    port = parsed.port or 443
    query = parse_qs(parsed.query)

    params = {k: v[0] for k, v in query.items()}
    return {
        "uuid": uuid,
        "host": host,
        "port": port,
        "security": params.get("security", "reality"),
        "flow": params.get("flow", "xtls-rprx-vision"),
        "encryption": params.get("encryption", "none"),
        "network": params.get("type", "tcp"),
        "sni": params.get("sni", ""),
        "pbk": params.get("pbk", ""),
        "sid": params.get("sid", ""),
        "fp": params.get("fp", "chrome"),
        "spx": params.get("spiderX", ""),
    }


class VPSChromeProxyManager:
    """Manages the full lifecycle of Chrome instances, Xray proxies, and anti-leak setups."""

    def __init__(self, executor: TargetExecutor):
        self.ex = executor

    def check_environment(self) -> dict:
        """Inspect host environment for GUI, XRDP, Chrome, Xray, and port status."""
        logger.info("Scanning target environment...")
        report = {
            "os_release": self.ex.run("cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"' || true"),
            "arch": self.ex.run("uname -m"),
            "current_user": self.ex.run("whoami"),
            "has_xfce": self.ex.command_exists("xfce4-session"),
            "has_xrdp": self.ex.command_exists("xrdp"),
            "has_chrome": self.ex.command_exists("google-chrome") or self.ex.command_exists("google-chrome-stable"),
            "has_xray": self.ex.command_exists("xray") or self.ex.file_exists("/usr/local/x-ui/bin/xray-linux-amd64"),
            "has_pproxy": self.ex.command_exists("pproxy") or self.ex.file_exists("/root/miniconda3/bin/pproxy"),
            "native_ip": self.ex.run("curl -s -m 5 https://api.ipify.org || echo 'Unknown'"),
            "xrdp_active": self.ex.run("systemctl is-active xrdp 2>/dev/null || echo 'inactive'") == "active",
        }
        logger.info(f"Environment scan result: OS={report['os_release']}, Native IP={report['native_ip']}, XRDP={report['xrdp_active']}")
        return report

    def setup_desktop_environment(self):
        """Install XFCE4, XRDP, and Chrome if missing; configure startwm.sh for stability."""
        logger.info("Ensuring XFCE4 desktop, XRDP, and Chrome are properly installed...")
        cmds = [
            "apt-get update -y",
            "DEBIAN_FRONTEND=noninteractive apt-get install -y xfce4 xfce4-goodies xrdp xorg dbus-x11 locales curl wget",
            "locale-gen en_US.UTF-8",
            "update-locale LANG=en_US.UTF-8",
        ]
        for c in cmds:
            self.ex.run(c)

        # Install Chrome if missing
        if not (self.ex.command_exists("google-chrome") or self.ex.command_exists("google-chrome-stable")):
            logger.info("Installing official Google Chrome Stable...")
            chrome_setup = (
                "wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && "
                "apt-get install -y /tmp/chrome.deb && rm -f /tmp/chrome.deb"
            )
            self.ex.run(chrome_setup)

        # Configure XRDP startwm.sh cleanly
        startwm_content = (
            "#!/bin/sh\n"
            "if [ -r /etc/default/locale ]; then\n"
            "  . /etc/default/locale\n"
            "  export LANG LANGUAGE\n"
            "fi\n"
            "unset DBUS_SESSION_BUS_ADDRESS\n"
            "unset XDG_RUNTIME_DIR\n"
            "exec startxfce4\n"
        )
        self.ex.write_file("/etc/xrdp/startwm.sh", startwm_content, mode="0755")
        self.ex.write_file("/root/.xsession", "xfce4-session\n", mode="0644")
        self.ex.run("systemctl restart xrdp && systemctl enable xrdp")
        logger.info("Desktop environment and XRDP configured successfully.")

    def ensure_xray_binary(self) -> str:
        """Locate or install official Xray binary."""
        if self.ex.file_exists("/usr/local/bin/xray"):
            return "/usr/local/bin/xray"
        if self.ex.file_exists("/usr/local/x-ui/bin/xray-linux-amd64"):
            self.ex.run("ln -sf /usr/local/x-ui/bin/xray-linux-amd64 /usr/local/bin/xray")
            return "/usr/local/bin/xray"

        logger.info("Downloading official Xray core...")
        dl_cmd = (
            "mkdir -p /tmp/xray && "
            "curl -sL https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip -o /tmp/xray/xray.zip && "
            "apt-get install -y unzip && unzip -q /tmp/xray/xray.zip -d /tmp/xray && "
            "mv /tmp/xray/xray /usr/local/bin/xray && chmod +x /usr/local/bin/xray && "
            "rm -rf /tmp/xray"
        )
        self.ex.run(dl_cmd)
        return "/usr/local/bin/xray"

    def setup_vless_proxy(
        self,
        vless_url: str,
        http_port: int = 2080,
        socks_port: int = 2081,
        service_name: str = "xray-client-us",
        config_dir: str = "/etc/xray-client-us",
    ) -> dict:
        """Configure and start Xray client service with VLESS + REALITY + Vision."""
        logger.info(f"Setting up VLESS proxy service '{service_name}' on port {http_port} (HTTP) / {socks_port} (SOCKS5)...")
        vless_info = parse_vless_url(vless_url)
        xray_bin = self.ensure_xray_binary()

        # Load config template
        tpl_path = TEMPLATES_DIR / "xray_vless_client.json.template"
        with open(tpl_path, "r", encoding="utf-8") as f:
            tpl_str = f.read()

        config_content = (
            tpl_str.replace("{LISTEN_ADDR}", "127.0.0.1")
            .replace("{HTTP_PORT}", str(http_port))
            .replace("{SOCKS_PORT}", str(socks_port))
            .replace("{REMOTE_HOST}", vless_info["host"])
            .replace("{REMOTE_PORT}", str(vless_info["port"]))
            .replace("{UUID}", vless_info["uuid"])
            .replace("{FLOW}", vless_info["flow"])
            .replace("{NETWORK}", vless_info["network"])
            .replace("{SECURITY}", vless_info["security"])
            .replace("{FINGERPRINT}", vless_info["fp"])
            .replace("{SERVER_NAME}", vless_info["sni"])
            .replace("{PUBLIC_KEY}", vless_info["pbk"])
            .replace("{SHORT_ID}", vless_info["sid"])
        )

        remote_cfg = f"{config_dir}/config.json"
        self.ex.write_file(remote_cfg, config_content, mode="0644")

        # Load service template
        svc_tpl_path = TEMPLATES_DIR / "xray_service.template"
        with open(svc_tpl_path, "r", encoding="utf-8") as f:
            svc_tpl_str = f.read()

        svc_content = (
            svc_tpl_str.replace("{SERVICE_TAG}", f"Port {http_port}")
            .replace("{XRAY_BIN}", xray_bin)
            .replace("{CONFIG_PATH}", remote_cfg)
        )

        service_file = f"/etc/systemd/system/{service_name}.service"
        self.ex.write_file(service_file, svc_content, mode="0644")

        # Reload and start service
        self.ex.run(f"systemctl daemon-reload && systemctl enable --now {service_name}.service")
        time.sleep(1.5)

        # Test exit IP through proxy
        exit_ip = self.ex.run(
            f"curl -s -m 8 -x http://127.0.0.1:{http_port} https://api.ipify.org || echo 'Error'"
        )
        logger.info(f"VLESS Proxy Service '{service_name}' started! Verified Exit IP: {exit_ip}")
        return {
            "service_name": service_name,
            "http_port": http_port,
            "socks_port": socks_port,
            "exit_ip": exit_ip,
        }

    def setup_residential_bridge(
        self,
        proxies: list,
        local_port: int = 18080,
        service_name: str = "proxy-bridge",
        script_path: str = "/root/Desktop/switch_proxy.sh",
    ):
        """Set up dynamic residential/datacenter proxy switcher via pproxy."""
        logger.info(f"Setting up Residential Proxy Bridge on port {local_port}...")

        # Ensure pproxy
        if not (self.ex.command_exists("pproxy") or self.ex.file_exists("/root/miniconda3/bin/pproxy")):
            self.ex.run("pip3 install pproxy || apt-get install -y python3-pip && pip3 install pproxy")

        # Format array for bash
        array_lines = []
        for p in proxies:
            array_lines.append(f'  "{p}"')
        proxies_array_str = "\n".join(array_lines)

        tpl_path = TEMPLATES_DIR / "switch_proxy.sh.template"
        with open(tpl_path, "r", encoding="utf-8") as f:
            tpl_str = f.read()

        script_content = (
            tpl_str.replace("{LOCAL_BRIDGE_PORT}", str(local_port))
            .replace("{BRIDGE_SERVICE_NAME}", service_name)
            .replace("{PROXIES_ARRAY}", proxies_array_str)
        )

        self.ex.write_file(script_path, script_content, mode="0755")

        # Start default node 1
        self.ex.run(f"{script_path} 1 || true")
        logger.info(f"Residential Proxy Switcher deployed at {script_path}")

    def create_chrome_instance(
        self,
        name: str = "US Proxy Chrome",
        profile_dir: str = "/root/.config/chrome-us-proxy",
        proxy_url: str = "http://127.0.0.1:2080",
        service_name: str = "xray-client-us.service",
        default_urls: list = None,
        launcher_path: str = "/root/Desktop/start_us_proxy_chrome.sh",
        desktop_entry_path: str = "/root/Desktop/us-proxy-chrome.desktop",
    ):
        """Create an isolated Chrome instance with anti-leak flags and desktop entry."""
        if default_urls is None:
            default_urls = ["https://ipinfo.io", "https://claude.ai"]

        wm_class = re.sub(r"[^a-zA-Z0-9_-]", "-", name.lower()).strip("-")
        logger.info(f"Creating isolated Chrome instance '{name}' (Profile: {profile_dir})...")

        # Launcher script
        urls_quoted = " ".join([f'"{u}"' for u in default_urls])
        launcher_tpl = TEMPLATES_DIR / "chrome_launcher.sh.template"
        with open(launcher_tpl, "r", encoding="utf-8") as f:
            l_str = f.read()

        launcher_content = (
            l_str.replace("{INSTANCE_NAME}", name)
            .replace("{USER_DATA_DIR}", profile_dir)
            .replace("{PROXY_URL}", proxy_url)
            .replace("{SERVICE_NAME}", service_name)
            .replace("{DEFAULT_URLS}", urls_quoted)
            .replace("{WM_CLASS}", wm_class)
        )
        self.ex.write_file(launcher_path, launcher_content, mode="0755")

        # Desktop entry
        desktop_tpl = TEMPLATES_DIR / "chrome_desktop.template"
        with open(desktop_tpl, "r", encoding="utf-8") as f:
            d_str = f.read()

        desktop_content = (
            d_str.replace("{INSTANCE_NAME}", name)
            .replace("{INSTANCE_COMMENT}", f"{name} - Anti-Leak Proxy Browser")
            .replace("{LAUNCHER_PATH}", launcher_path)
            .replace("{WM_CLASS}", wm_class)
        )
        self.ex.write_file(desktop_entry_path, desktop_content, mode="0755")
        logger.info(f"Chrome instance '{name}' configured. Desktop entry: {desktop_entry_path}")

        # Deploy Enterprise Policy for WebRTC non-proxied UDP restriction
        policy_dir = "/etc/opt/chrome/policies/managed"
        self.ex.run(f"mkdir -p {policy_dir}")
        policy_content = json.dumps({"WebRtcIPHandlingPolicy": "disable_non_proxied_udp"}, indent=2)
        self.ex.write_file(f"{policy_dir}/webrtc_policy.json", policy_content, mode="0644")

        # Kernel-level STUN packet drop to prevent WebRTC leaks
        self.ex.run(
            "iptables -C OUTPUT -p udp -m multiport --dports 3478,5349,19302 -j REJECT 2>/dev/null || "
            "iptables -I OUTPUT -p udp -m multiport --dports 3478,5349,19302 -j REJECT || true"
        )

    def test_leak_and_status(self, proxy_port: int = 2080) -> dict:
        """Perform automated leak verification (DNS, WebRTC, QUIC, AI connectivity)."""
        logger.info("Executing leak test and connectivity suite...")

        native_ip = self.ex.run("curl -s -m 5 https://api.ipify.org || echo 'Unknown'")
        proxy_ip = self.ex.run(f"curl -s -m 8 -x http://127.0.0.1:{proxy_port} https://api.ipify.org || echo 'Failed'")
        ipinfo_raw = self.ex.run(f"curl -s -m 8 -x http://127.0.0.1:{proxy_port} https://ipinfo.io/json || echo '{{}}'")

        try:
            ipinfo = json.loads(ipinfo_raw)
        except Exception:
            ipinfo = {}

        # Chrome Headless Test
        chrome_ip_cmd = (
            "google-chrome-stable --headless=new --no-sandbox --disable-dev-shm-usage "
            f'--proxy-server="http://127.0.0.1:{proxy_port}" --disable-quic '
            "--webrtc-ip-handling-policy=disable_non_proxied_udp --enforce-webrtc-ip-permission-check "
            '--dump-dom "https://api.ipify.org" 2>/dev/null | grep -oE "([0-9]{1,3}\\.){3}[0-9]{1,3}" | head -n 1 || echo "Failed"'
        )
        chrome_ip = self.ex.run(chrome_ip_cmd)

        # AI endpoint connectivity
        anthropic_ok = "200" in self.ex.run(f"curl -s -m 8 -x http://127.0.0.1:{proxy_port} -I https://api.anthropic.com || true")
        openai_ok = "200" in self.ex.run(f"curl -s -m 8 -x http://127.0.0.1:{proxy_port} -I https://api.openai.com || true")

        results = {
            "native_ip": native_ip,
            "proxy_ip": proxy_ip,
            "chrome_rendered_ip": chrome_ip,
            "country": ipinfo.get("country", "Unknown"),
            "city": ipinfo.get("city", "Unknown"),
            "org": ipinfo.get("org", "Unknown"),
            "anthropic_accessible": anthropic_ok,
            "openai_accessible": openai_ok,
            "is_leak_free": (proxy_ip != native_ip) and (chrome_ip == proxy_ip),
        }
        logger.info(f"Leak Test Results: {json.dumps(results, indent=2)}")
        return results

    def generate_cheat_sheet(
        self,
        target_host: str,
        native_ip: str,
        active_proxy_ip: str,
        active_country: str,
        http_port: int,
        socks_port: int,
        service_name: str,
        chrome_instances: list,
        output_paths: list = None,
    ):
        """Generate and save local usage cheat sheet for instant cat reading."""
        if output_paths is None:
            output_paths = ["/root/Desktop/PROXY_CHEAT_SHEET.txt", "/root/proxy_cheat_sheet.txt"]

        instances_formatted = []
        for inst in chrome_instances:
            instances_formatted.append(
                f"* [{inst['name']}]\n"
                f"  - 启动脚本: {inst['launcher']}\n"
                f"  - 桌面图标: {inst['desktop']}\n"
                f"  - 独立目录: {inst['profile']}\n"
                f"  - 代理配置: {inst['proxy']}"
            )
        instances_str = "\n".join(instances_formatted)

        tpl_path = TEMPLATES_DIR / "proxy_cheat_sheet.txt.template"
        with open(tpl_path, "r", encoding="utf-8") as f:
            tpl_str = f.read()

        sheet_content = (
            tpl_str.replace("{TARGET_HOST}", target_host)
            .replace("{DEPLOY_DATE}", time.strftime("%Y-%m-%d %H:%M:%S"))
            .replace("{NATIVE_IP}", native_ip)
            .replace("{ACTIVE_PROXY_IP}", active_proxy_ip)
            .replace("{ACTIVE_COUNTRY}", active_country)
            .replace("{HTTP_PORT}", str(http_port))
            .replace("{SOCKS_PORT}", str(socks_port))
            .replace("{SERVICE_NAME}", service_name)
            .replace("{CHROME_INSTANCES_LIST}", instances_str)
        )

        for p in output_paths:
            self.ex.write_file(p, sheet_content, mode="0644")
        logger.info(f"Cheat sheet written to: {', '.join(output_paths)}")
        return sheet_content


def build_parser():
    parser = argparse.ArgumentParser(
        description="VPS Chrome Proxy Automation Engine - Deploy Anti-Leak Chrome & Gateways."
    )
    # Target Connection
    parser.add_argument("--local", action="store_true", default=True, help="Operate directly on localhost (default: True)")
    parser.add_argument("--ssh-host", help="Remote SSH hostname / IP")
    parser.add_argument("--ssh-port", type=int, default=22, help="Remote SSH port (default: 22)")
    parser.add_argument("--ssh-user", default="root", help="Remote SSH username (default: root)")
    parser.add_argument("--ssh-pass", help="Remote SSH password")
    parser.add_argument("--ssh-key", help="Remote SSH private key path")

    # Subcommands / Actions
    parser.add_argument("--check-env", action="store_true", help="Run environment check")
    parser.add_argument("--setup-desktop", action="store_true", help="Install & configure XFCE4, XRDP, and Chrome")
    parser.add_argument("--add-vless", help="VLESS URL (e.g. vless://uuid@host:port?...)")
    parser.add_argument("--http-port", type=int, default=2080, help="Local HTTP proxy port (default: 2080)")
    parser.add_argument("--socks-port", type=int, default=2081, help="Local SOCKS5 proxy port (default: 2081)")
    parser.add_argument("--service-name", default="xray-client-us", help="Systemd service name")

    # Chrome creation
    parser.add_argument("--chrome-name", default="US Proxy Chrome", help="Name of Chrome instance")
    parser.add_argument("--chrome-profile", default="/root/.config/chrome-us-proxy", help="User data dir for Chrome")
    parser.add_argument("--chrome-launcher", default="/root/Desktop/start_us_proxy_chrome.sh", help="Launcher script path")
    parser.add_argument("--chrome-desktop", default="/root/Desktop/us-proxy-chrome.desktop", help="Desktop entry path")

    # All-in-one execution
    parser.add_argument("--all-in-one", action="store_true", help="Run complete setup, leak test, and generate cheat sheet")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    is_local = not bool(args.ssh_host)
    executor = TargetExecutor(
        is_local=is_local,
        host=args.ssh_host or "127.0.0.1",
        port=args.ssh_port,
        user=args.ssh_user,
        password=args.ssh_pass,
        key_file=args.ssh_key,
    )
    manager = VPSChromeProxyManager(executor)

    if args.check_env:
        report = manager.check_environment()
        print(json.dumps(report, indent=2))
        return

    if args.setup_desktop:
        manager.setup_desktop_environment()

    if args.add_vless:
        manager.setup_vless_proxy(
            vless_url=args.add_vless,
            http_port=args.http_port,
            socks_port=args.socks_port,
            service_name=args.service_name,
        )

    if args.all_in_one:
        logger.info("Starting All-in-One Automated Provisioning...")
        env = manager.check_environment()
        if not (env["has_xfce"] and env["has_xrdp"] and env["has_chrome"]):
            manager.setup_desktop_environment()

        proxy_info = {}
        if args.add_vless:
            proxy_info = manager.setup_vless_proxy(
                vless_url=args.add_vless,
                http_port=args.http_port,
                socks_port=args.socks_port,
                service_name=args.service_name,
            )

        manager.create_chrome_instance(
            name=args.chrome_name,
            profile_dir=args.chrome_profile,
            proxy_url=f"http://127.0.0.1:{args.http_port}",
            service_name=f"{args.service_name}.service",
            launcher_path=args.chrome_launcher,
            desktop_entry_path=args.chrome_desktop,
        )

        leak_results = manager.test_leak_and_status(proxy_port=args.http_port)

        chrome_instances = [
            {
                "name": args.chrome_name,
                "launcher": args.chrome_launcher,
                "desktop": args.chrome_desktop,
                "profile": args.chrome_profile,
                "proxy": f"http://127.0.0.1:{args.http_port}",
            }
        ]
        sheet = manager.generate_cheat_sheet(
            target_host=args.ssh_host or "localhost",
            native_ip=leak_results.get("native_ip", "Unknown"),
            active_proxy_ip=leak_results.get("proxy_ip", "Unknown"),
            active_country=leak_results.get("country", "US"),
            http_port=args.http_port,
            socks_port=args.socks_port,
            service_name=args.service_name,
            chrome_instances=chrome_instances,
        )
        print("\n" + sheet)


if __name__ == "__main__":
    main()
