"""
粥粥的表情转换脚本
把 layered (14帧) → matrix (90帧) 非分层格式
避开 firmware v1.16.0 的 layered 渲染重影 bug
"""

import struct, sys, os
from pathlib import Path

W, H = 240, 80
FRAME_BYTES = W * H * 2  # RGB565 = 2 bytes/pixel

EXPRESSIONS = ["idle", "happy", "thinking", "sad", "surprised", "embarrassed"]


def load_raw(path):
    return Path(path).read_bytes()


def save_raw(path, data):
    Path(path).write_bytes(data)
    print(f"Saved: {path} ({len(data):,} bytes, {len(data)//FRAME_BYTES} frames)")


def extract_frames(data):
    """Extract individual 240x80 RGB565 frames from raw data"""
    n = len(data) // FRAME_BYTES
    frames = []
    for i in range(n):
        off = i * FRAME_BYTES
        frames.append(data[off:off + FRAME_BYTES])
    return frames


def rgb565_to_rgba(frame):
    """Convert single RGB565 frame to RGBA pixel list"""
    pixels = []
    for i in range(0, len(frame), 2):
        val = struct.unpack('<H', frame[i:i+2])[0]
        r = ((val >> 11) & 0x1F) << 3
        g = ((val >> 5) & 0x3F) << 2
        b = (val & 0x1F) << 3
        a = 0 if val == 0 else 255
        pixels.append((r, g, b, a))
    return pixels


def rgba_to_rgb565(pixels):
    """Convert RGBA pixel list back to single RGB565 frame"""
    data = bytearray()
    for r, g, b, a in pixels:
        if a == 0:
            data.extend(struct.pack('<H', 0))
        else:
            val = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
            data.extend(struct.pack('<H', val))
    return bytes(data)


def composite_layers(base_frame, overlay_frame):
    """Composite overlay on top of base (overlay non-zero pixels replace base)"""
    base_px = rgb565_to_rgba(base_frame)
    overlay_px = rgb565_to_rgba(overlay_frame)
    result = []
    for b, o in zip(base_px, overlay_px):
        if o[3] > 0:  # overlay pixel is non-transparent
            result.append(o)
        else:
            result.append(b)
    return rgba_to_rgb565(result)


def analyze_layered(frames):
    """Analyze how layered format is structured"""
    n = len(frames)
    print(f"\n=== Analyzing {n} frames ===")
    for i, f in enumerate(frames):
        nz = sum(1 for j in range(0, len(f), 2) if struct.unpack('<H', f[j:j+2])[0] != 0)
        print(f"  Frame {i:2d}: {nz:5d} non-zero pixels")

    # Try to figure out layer organization
    # Check which frames are identical
    print("\n=== Frame similarity ===")
    for i in range(n):
        for j in range(i+1, n):
            if frames[i] == frames[j]:
                print(f"  Frame {i} == Frame {j}")


def layered_to_single(frames):
    """
    Convert layered format to single (non-layered) format.

    Current understanding:
    - 14 frames in layered format
    - Frames 0-5: 6 expressions (base/detail layers)
    - Frames 6-13: overlay layers (all copies of frame 0 in v6)

    Non-layered output:
    - Just the 6 unique expression frames, each pre-composited
    """
    n = len(frames)

    if n == 14:
        # Layered format: 6 expressions × 2 layers + 2 extras
        # v6 attempt made all overlay layers = frame 0
        # But originally: layer0=base shapes, layer1=expression-specific details

        # For non-layered, we take the 6 unique expression base frames
        # These ARE the complete face drawings, just without compositing
        single_frames = frames[0:6]
        print(f"\nExtracted {len(single_frames)} expression frames from layered format")
        return single_frames

    elif n <= 10:
        # Already non-layered or small set
        return frames

    else:
        # Unknown format - just take unique frames
        seen = []
        unique = []
        for f in frames:
            if f not in seen:
                seen.append(f)
                unique.append(f)
        print(f"\nFound {len(unique)} unique frames out of {n}")
        return unique


def create_matrix_format(expression_frames, total_frames=90):
    """
    Create matrix format: pad/repeat expression frames to fill 90 frames.

    Matrix format structure (educated guess):
    - Each expression has a dedicated frame index
    - 90 frames total for the full animation set
    - We fill our 6 expressions into the first 6 slots, rest = idle copies

    Expression mapping (by index):
    0=idle, 1=happy, 2=thinking, 3=sad, 4=surprised, 5=embarrassed
    """
    n_expr = len(expression_frames)
    result = bytearray()

    for i in range(total_frames):
        if i < n_expr:
            result.extend(expression_frames[i])
        else:
            # Fill remaining with idle (frame 0)
            result.extend(expression_frames[0])

    return bytes(result)


def main():
    input_path = Path(__file__).parent / "avatar_layered.raw"
    if not input_path.exists():
        print(f"ERROR: {input_path} not found")
        sys.exit(1)

    print(f"Reading: {input_path}")
    data = load_raw(input_path)
    frames = extract_frames(data)

    analyze_layered(frames)

    # Convert to single (non-layered) expression frames
    single_frames = layered_to_single(frames)

    # Save non-layered 6-frame version
    single_data = b''.join(single_frames)
    single_path = Path(__file__).parent / "avatar_single.raw"
    save_raw(single_path, single_data)

    # Create matrix format (90 frames)
    matrix_data = create_matrix_format(single_frames, total_frames=90)
    matrix_path = Path(__file__).parent / "avatar_matrix.raw"
    save_raw(matrix_path, matrix_data)

    print(f"\n=== Summary ===")
    print(f"Layered:    {len(frames)} frames, {len(data):,} bytes")
    print(f"Single:     {len(single_frames)} frames, {len(single_data):,} bytes")
    print(f"Matrix:     90 frames, {len(matrix_data):,} bytes")
    print(f"\nExpressions: {EXPRESSIONS[:len(single_frames)]}")
    print(f"\nNext steps:")
    print(f"  1. Upload avatar_matrix.raw to VPS ~/avatar_matrix.raw")
    print(f"  2. Call load_avatar_set(archive_path='/home/ubuntu/avatar_matrix.raw', mode='matrix')")


if __name__ == "__main__":
    main()
