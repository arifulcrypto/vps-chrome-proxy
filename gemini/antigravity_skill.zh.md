# Antigravity (AGY) 技能适配器：VPS Chrome 代理引擎

本技能适配 Google Antigravity Agentic 架构，为 Linux VPS 与 LXC 容器提供高可靠、防泄漏的独立浏览器与多轨网关环境。

- **核心执行脚本**：`scripts/vps_chrome_proxy.py`
- **配置模板库**：`templates/`
- **规范定义文档**：`SKILL.md`

## 推荐工作流：
1. 先行执行 `check-env` 探测系统版本、CPU 架构与现有服务端口；
2. 若缺少桌面套件，调用 `setup-desktop` 完成静默安装；
3. 根据用户输入，执行 `setup-vless` 或 `setup-residential` 创建独立的后台服务；
4. 执行 `create-chrome` 生成带全套防泄漏参数的桌面快捷方式与专属 Profile；
5. 执行 `test-leak` 校验出口 IP 并确认 DNS 与 WebRTC 无泄漏。
