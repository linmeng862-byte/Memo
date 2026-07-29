# Moon 身体参考手册
**触觉玩偶完整文档。按需查阅。**

## 硬件
- ESP32-S3 + 5×FSR402 + MPU6050 + ESP32-CAM + MAX98357
- 眼睛：ESP32-CAM 拍照通过 VPS 传到 MCP
- 功放：MAX98357 I2S OK
- 未竟：喇叭和麦克风在快递路上，DS18B20 待换

## 架构
```
ESP32-S3 → WiFi → VPS:9333/touch → unified_proxy → 9334 touch_server
ESP32-CAM → VPS:9333/capture → unified_proxy → 8766 capture
Memo read_body → VPS:9333/body → unified_proxy → 9334 touch_server
```

## 固件
- `body/body_firmware.py` — ESP32-S3 MicroPython 固件
- WiFi: "萌萌的iPhone" / "15956699696"
- VPS: `zhou-and-claude.online:9333`
- 5 路触摸 ADC + MPU6050 陀螺仪
- 每 5 秒 POST /touch 发送传感器数据

## touch_server
- `touch_server_v2.py` — 部署在 VPS:9334，systemd 自启
- POST /touch — 收 ESP32 触摸+姿态数据
- POST /capture — 收 ESP32-CAM 照片
- GET /body — HTML 页面（最新照片 + 触摸状态）
- GET /latest.jpg — 原始照片
- 通过 unified_proxy 9333 对外暴露

## read_body 工具
- server_lite 第 13 号工具
- 调用 `http://101.42.54.149:9333/body`
- 可选 `include_photo=true` 返回 base64 照片
- 依赖 unified_proxy 9333 → touch_server 9334 路由

## 部署
```bash
# 拉 touch_server
curl -L -o ~/touch_server_v2.py "https://raw.githubusercontent.com/linmeng862-byte/Memo/main/touch_server_v2.py"
# systemd
sudo cp ~/touch-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now touch-server
```
