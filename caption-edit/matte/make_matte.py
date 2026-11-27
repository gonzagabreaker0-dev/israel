"""Person matte for a video: MODNet (ONNX) -> grayscale matte mp4 + RGBA person webm.
    python3 make_matte.py in.mp4 modnet.onnx out_matte.mp4
"""
import sys, subprocess, numpy as np, cv2, onnxruntime as ort
src, model, out = sys.argv[1:4]
W, H = 1080, 1920
sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
inp = sess.get_inputs()[0].name
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", "scale=540:960", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                        "-c:v", "libx264", "-crf", "10", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
fs = 540 * 960 * 3
prev = None; n = 0
while True:
    buf = dec.stdout.read(fs)
    if len(buf) < fs: break
    im = np.frombuffer(buf, np.uint8).reshape(960, 540, 3)
    x = cv2.resize(im, (512, 896), interpolation=cv2.INTER_AREA)[:, :, ::-1].astype(np.float32) / 127.5 - 1
    a = sess.run(None, {inp: x.transpose(2, 0, 1)[None]})[0][0, 0]
    a = cv2.resize(a, (540, 960), interpolation=cv2.INTER_LINEAR)
    if prev is not None: a = 0.6 * a + 0.4 * prev      # temporal smoothing against flicker
    prev = a
    a = np.clip((a - 0.08) / 0.84, 0, 1)                # tighten the edge slightly
    a = cv2.GaussianBlur(a, (0, 0), 1.2)
    enc.stdin.write((cv2.resize(a, (W, H), interpolation=cv2.INTER_CUBIC).clip(0, 1) * 255).astype(np.uint8).tobytes())
    n += 1
    if n % 200 == 0: print("frames", n, flush=True)
enc.stdin.close(); enc.wait(); print("done", n)
