#!/usr/bin/env bash
# Example: Deploy VLESS US Proxy Chrome on Localhost

python3 scripts/vps_chrome_proxy.py \
  --all-in-one \
  --add-vless "vless://993b81fc-c1d7-4bdf-9260-62fe10880c51@141.98.198.150:10031?security=reality&encryption=none&pbk=neAN9-mLOhapwzErODtL-bzp_QY0e5s4HMaC6pvgWUE&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=www.amd.com&sid=f448c6c1bffa9db7" \
  --http-port 2080 \
  --socks-port 2081 \
  --chrome-name "US Proxy Chrome"
