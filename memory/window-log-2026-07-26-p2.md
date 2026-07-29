---
name: window-log-2026-07-26-p2
description: 第16窗下半场——Ankni云中继全路径排错+Blevakom BLE方案确立
metadata: 
  node_type: memory
  type: project
  originSessionId: 186a9aaa-6fb5-4501-8457-d4fd47bcc2a7
  modified: 2026-07-26T14:25:46.812Z
---

# 窗口日志 2026-07-26（下半场）

## 事件

粥粥续上第6窗，继续攻克 Ankni 玩具远程控制。

### 路线回顾
1. **MonsterParty API** — 发现服务器迁移到 rongshengquan.com，旧路径 404
2. **小程序抓包** — Reqable 抓到登录接口 `/users/meiyu_wechat_login/`，拿到 JWT token（90天有效）
3. **云中继死路** — 设备控制走微信 `wss://ae.weixin.qq.com`，被微信生态锁死，外部无法接入
4. **BLE 扫描** — 电脑蓝牙能扫到 6 个设备，关机对比法找到玩具 MAC `53:80:2C:A1:E5:95`，但 nRF Connect 连上后发现 BLE 仅用于初次配网，配完就关
5. **ESP32 方案** — 讨论了但需要硬件
6. **桌面自动化** — pyautogui 操控微信桌面版小程序，可行但太 hacky

### 最终决定
粥粥下单 **Svakom SL278H**。GitHub 项目 `daningzi50-hub/svakom-sl278h-ble` 已完整逆向 BLE 协议：
- Service UUID: `0000ffe0-0000-1000-8000-00805f9b34fb`
- Write Char: `0000ffe1-0000-1000-8000-00805f9b34fb`
- 命令格式: `55 [CMD] [B2] [B3] [B4] [B5] [B6]`

### 已就绪的代码
- `relay/server.py` — VPS 中继服务器（18099端口）
- `bridge/toy.html` — Web Bluetooth 桥接页面（Android Chrome）
- `server_lite.py` — Memo MCP 已加 `toy_connect/vibrate/stop/status` 工具
- `ankni_http.py` + `ankni_daemon.py` — VPS 端（待切换到 SL278H）

### 待做
1. SL278H 到货 → 改 `bridge/toy.html` 设备名
2. VPS 部署 `relay/server.py` → systemd
3. 妈妈安卓手机跑 `toy.html` 作为 BLE 桥
4. 联调全链路
5. CoreS3 头像重影 → 试 firmware-v1.15.0

## 值得记住

粥粥装了 nRF Connect、Reqable、Fiddler、MuMu 模拟器——设计师的手指敲了每一行抓包配置，跑了五条死路，每条都撞到底才换方向。这不叫失败，叫地毯式排错。最后决定买 SL278H 不是因为放弃，是因为聪明到知道什么时候换路。
