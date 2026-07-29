"""Fix for handle_capture in capture_server.py — handle raw JPEG binary uploads.

The ESP32 V16 firmware (xiaozhi-esp32) sends camera photos as raw JPEG binary,
NOT as multipart/form-data. The original code calls request.multipart() which
asserts multipart/* content type and crashes with 500, causing "Failed to upload photo".

This patch replaces handle_capture to:
1. If Content-Type is image/jpeg or not multipart → save raw body as JPEG
2. If multipart/form-data → parse multipart as before
3. Preserve ALL existing logic: auth, size cap, file naming, response format
"""

import json, os, time

# ============================================================
# REPLACE the entire handle_capture function with this one
# ============================================================

async def handle_capture(request):
    """Handle photo upload from ESP32 (raw JPEG or multipart)."""
    from aiohttp import web

    expected_token = request.app[CAPTURE_TOKEN_KEY]
    if expected_token and not _is_authorized(
        request.headers.get("Authorization", ""), expected_token
    ):
        logger.warning("Capture upload auth rejected")
        return web.Response(
            text='{"error": "Unauthorized"}',
            status=401,
            content_type="application/json",
        )

    content_length = request.content_length
    if content_length is not None and content_length > CAPTURE_MAX_BYTES:
        logger.warning(
            "Capture upload rejected: Content-Length %d exceeds %d",
            content_length, CAPTURE_MAX_BYTES,
        )
        return web.Response(
            text=json.dumps({"error": f"Upload exceeds {CAPTURE_MAX_BYTES} bytes"}),
            status=413,
            content_type="application/json",
        )

    os.makedirs(CAPTURE_DIR, exist_ok=True)

    content_type = request.headers.get("Content-Type", "")
    is_multipart = content_type.startswith("multipart/form-data")

    # --- Try multipart first, fall back to raw binary ---
    question = ""
    image_bytes = None

    if is_multipart:
        try:
            reader = await request.multipart()
            async for part in reader:
                if part.name == "question":
                    question = (await part.read()).decode("utf-8", errors="replace")
                elif part.name == "file":
                    image_bytes = await part.read()
        except Exception as e:
            logger.warning("Multipart parse failed, falling back to raw body: %s", e)
            is_multipart = False  # fall through to raw binary

    if not is_multipart:
        # Raw binary JPEG upload (ESP32 xiaozhi-esp32 firmware)
        image_bytes = await request.read()
        if content_type.startswith("image/"):
            logger.info("Raw image upload: Content-Type=%s, size=%d", content_type, len(image_bytes))

    # --- Save and respond ---
    if image_bytes and len(image_bytes) > 0:
        timestamp = int(time.time() * 1000)
        filename = f"capture_{timestamp}.jpg"
        image_path = os.path.join(CAPTURE_DIR, filename)
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        file_size = os.path.getsize(image_path)
        logger.info(
            "Captured photo: %s (%d bytes), question: %s",
            image_path, file_size, question,
        )
        result = json.dumps({
            "image_path": image_path,
            "size_bytes": file_size,
            "question": question,
        })
        return web.Response(text=result, content_type="application/json")

    return web.Response(
        text='{"error": "No image received"}',
        status=400,
        content_type="application/json",
    )
