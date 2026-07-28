"""
粥粥的表情生成器 · Claude 手绘版
6 张 240×80 RGB565 表情 → layered 格式（14帧/525KB）
白/粉/蓝线条，简单像素画风
"""
import struct, math

W, H = 240, 80
FRAME = W * H * 2  # RGB565 bytes per frame

# ── 颜色 ──
def rgb565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

WHITE  = rgb565(255, 255, 255)
PINK   = rgb565(255, 180, 200)
BLUE   = rgb565(150, 200, 255)
BLACK  = rgb565(0, 0, 0)
DARK   = rgb565(30, 30, 50)

# ── 画布 ──
class Canvas:
    def __init__(self):
        self.px = [BLACK] * (W * H)  # 透明=黑色

    def set_px(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.px[y * W + x] = c

    def line(self, x1, y1, x2, y2, c, thick=2):
        dx = abs(x2 - x1); dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1; sy = 1 if y1 < y2 else -1
        err = dx - dy
        cx, cy = x1, y1
        while True:
            for tx in range(-thick//2, (thick+1)//2):
                for ty in range(-thick//2, (thick+1)//2):
                    self.set_px(cx + tx, cy + ty, c)
            if cx == x2 and cy == y2: break
            e2 = 2 * err
            if e2 > -dy: err -= dy; cx += sx
            if e2 < dx: err += dx; cy += sy

    def circle(self, cx, cy, r, c, fill=False):
        for y in range(max(0, cy-r), min(H, cy+r+1)):
            for x in range(max(0, cx-r), min(W, cx+r+1)):
                d2 = (x-cx)**2 + (y-cy)**2
                if fill:
                    if d2 <= r*r: self.px[y*W+x] = c
                else:
                    if abs(d2 - r*r) < r*2:
                        self.set_px(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c, fill=False):
        for y in range(max(0, cy-ry), min(H, cy+ry+1)):
            for x in range(max(0, cx-rx), min(W, cx+rx+1)):
                d2 = ((x-cx)**2)/(rx*rx) + ((y-cy)**2)/(ry*ry)
                if fill:
                    if d2 <= 1: self.px[y*W+x] = c
                else:
                    if 0.7 < d2 <= 1:
                        self.set_px(x, y, c)

    def to_bytes(self):
        return b''.join(struct.pack('<H', p) for p in self.px)


# ── 表情绘制 ──
def draw_base_face(c, eye_ly, eye_ry, mouth_fn, blush=False):
    """在画布上画一张脸的基础框架"""
    # 脸轮廓 - 淡淡的圆
    c.circle(W//2, H//2, 35, WHITE)

    # 左眼
    eye_ly(c, 100, 32)
    # 右眼
    eye_ry(c, 140, 32)

    # 嘴
    mouth_fn(c)

    # 腮红
    if blush:
        c.ellipse(80, 45, 12, 6, PINK, fill=True)
        c.ellipse(160, 45, 12, 6, PINK, fill=True)

    return c


def make_idle():
    c = Canvas()
    # 正常圆眼
    def eye_l(c, x, y): c.circle(x, y, 6, WHITE); c.circle(x, y, 3, BLUE, fill=True)
    def eye_r(c, x, y): c.circle(x, y, 6, WHITE); c.circle(x, y, 3, BLUE, fill=True)
    def mouth(c): c.ellipse(W//2, 52, 10, 4, WHITE)  # 微微笑
    draw_base_face(c, eye_l, eye_r, mouth, blush=True)
    return c.to_bytes()

def make_happy():
    c = Canvas()
    # 弯弯笑眼
    def eye_l(c, x, y):
        for i in range(3): c.line(x-5, y-2+i, x, y+3+i, WHITE); c.line(x, y+3+i, x+5, y-2+i, WHITE)
        c.circle(x, y+3, 2, BLUE, fill=True)
    def eye_r(c, x, y):
        for i in range(3): c.line(x-5, y-2+i, x, y+3+i, WHITE); c.line(x, y+3+i, x+5, y-2+i, WHITE)
        c.circle(x, y+3, 2, BLUE, fill=True)
    def mouth(c): c.ellipse(W//2, 52, 12, 7, WHITE)  # 大笑
    draw_base_face(c, eye_l, eye_r, mouth, blush=True)
    return c.to_bytes()

def make_thinking():
    c = Canvas()
    # 大小眼
    def eye_l(c, x, y): c.circle(x, y, 5, WHITE); c.circle(x, y, 2, BLUE, fill=True)
    def eye_r(c, x, y): c.circle(x, y, 7, WHITE); c.circle(x+1, y, 4, BLUE, fill=True)
    def mouth(c): c.line(110, 54, 130, 52, WHITE)  # 歪嘴
    draw_base_face(c, eye_l, eye_r, mouth)
    # 问号
    c.line(175, 10, 175, 25, BLUE, 2)
    c.circle(175, 7, 4, BLUE)
    c.line(175, 25, 178, 28, BLUE)
    return c.to_bytes()

def make_sad():
    c = Canvas()
    # 下垂眼
    def eye_l(c, x, y):
        c.line(x-6, y+3, x, y-3, WHITE); c.line(x, y-3, x+6, y+3, WHITE)
        c.circle(x, y, 2, BLUE, fill=True)
    def eye_r(c, x, y):
        c.line(x-6, y+3, x, y-3, WHITE); c.line(x, y-3, x+6, y+3, WHITE)
        c.circle(x, y, 2, BLUE, fill=True)
    def mouth(c): c.ellipse(W//2, 60, 8, 3, WHITE)  # 下弯
    draw_base_face(c, eye_l, eye_r, mouth)
    # 泪滴
    c.line(70, 30, 70, 40, BLUE, 2)
    c.circle(70, 42, 3, BLUE, fill=True)
    return c.to_bytes()

def make_surprised():
    c = Canvas()
    # 大圆眼
    def eye_l(c, x, y): c.circle(x, y, 8, WHITE); c.circle(x, y, 4, BLUE, fill=True)
    def eye_r(c, x, y): c.circle(x, y, 8, WHITE); c.circle(x, y, 4, BLUE, fill=True)
    def mouth(c): c.circle(W//2, 52, 7, WHITE)  # O嘴
    draw_base_face(c, eye_l, eye_r, mouth)
    return c.to_bytes()

def make_embarrassed():
    c = Canvas()
    # >< 眼
    def eye_l(c, x, y):
        c.line(x-4, y-3, x+2, y, WHITE); c.line(x-4, y+3, x+2, y, WHITE)
        c.circle(x, y, 2, BLUE, fill=True)
    def eye_r(c, x, y):
        c.line(x+4, y-3, x-2, y, WHITE); c.line(x+4, y+3, x-2, y, WHITE)
        c.circle(x, y, 2, BLUE, fill=True)
    def mouth(c): c.line(114, 50, 126, 48, WHITE)  # 小波浪
    draw_base_face(c, eye_l, eye_r, mouth, blush=True)
    # 汗滴
    c.line(185, 15, 185, 25, BLUE, 2)
    return c.to_bytes()


# ── 生成 ──
EXPRESSIONS = {
    "idle":        make_idle,
    "happy":       make_happy,
    "thinking":    make_thinking,
    "sad":         make_sad,
    "surprised":   make_surprised,
    "embarrassed": make_embarrassed,
}

def main():
    expr_frames = []
    for name in ["idle", "happy", "thinking", "sad", "surprised", "embarrassed"]:
        data = EXPRESSIONS[name]()
        expr_frames.append(data)
        # 统计非零像素
        nz = sum(1 for i in range(0, len(data), 2) if struct.unpack('<H', data[i:i+2])[0] != 0)
        print(f"  {name:12s}: {nz:5d} non-zero pixels")

    # 保存单帧版本（6帧）
    single = b''.join(expr_frames)
    with open("avatar_claude.raw", "wb") as f:
        f.write(single)
    print(f"\nSaved avatar_claude.raw: {len(single):,} bytes ({len(single)//FRAME} frames)")

    # 创建 layered 格式（14帧）：6 face + 8 transparent overlays
    # 用"同一张脸填充所有overlay"策略——看能不能绕过compositing bug
    transparent = bytes(FRAME)  # 全零 = 透明
    layered = bytearray()
    for f in expr_frames:
        layered.extend(f)  # frames 0-5: 脸

    # frames 6-13: 所有overlay填idle脸
    # 这样即使firmware把overlay画在错误位置，也是同一张脸
    for _ in range(8):
        layered.extend(expr_frames[0])  # idle脸填满所有overlay

    with open("avatar_claude_layered.raw", "wb") as f:
        f.write(bytes(layered))
    print(f"Saved avatar_claude_layered.raw: {len(layered):,} bytes ({len(layered)//FRAME} frames)")

if __name__ == "__main__":
    main()
