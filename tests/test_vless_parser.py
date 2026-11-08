import pytest
from scripts.vps_chrome_proxy import parse_vless_url

def test_parse_vless_url():
    test_url = (
        "vless://993b81fc-c1d7-4bdf-9260-62fe10880c51@141.98.198.150:10031"
        "?security=reality&encryption=none&pbk=neAN9-mLOhapwzErODtL-bzp_QY0e5s4HMaC6pvgWUE"
        "&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=www.amd.com&sid=f448c6c1bffa9db7"
    )
    result = parse_vless_url(test_url)
    assert result["uuid"] == "993b81fc-c1d7-4bdf-9260-62fe10880c51"
    assert result["host"] == "141.98.198.150"
    assert result["port"] == 10031
    assert result["security"] == "reality"
    assert result["flow"] == "xtls-rprx-vision"
    assert result["encryption"] == "none"
    assert result["network"] == "tcp"
    assert result["sni"] == "www.amd.com"
    assert result["pbk"] == "neAN9-mLOhapwzErODtL-bzp_QY0e5s4HMaC6pvgWUE"
    assert result["sid"] == "f448c6c1bffa9db7"
    assert result["fp"] == "chrome"

def test_invalid_scheme():
    with pytest.raises(ValueError):
        parse_vless_url("vmess://something")
