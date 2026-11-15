"""Procedural sounds for the desk: paper, cards, pen, seal, page, a quiet room.
Run: python3 tools/audio/make_sounds.py  -> assets/audio/*.ogg (via ffmpeg)."""
import numpy as np, subprocess, tempfile, os
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "audio")
rng = np.random.default_rng(7)

def bp(x, lo, hi, order=2):
    b, a = butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band")
    return lfilter(b, a, x)

def lp(x, hi, order=2):
    b, a = butter(order, hi / (SR / 2), btype="low")
    return lfilter(b, a, x)

def env(n, attack, decay):
    t = np.arange(n) / SR
    e = np.minimum(t / max(attack, 1e-4), 1.0) * np.exp(-t / decay)
    return e

def noise(sec):
    return rng.standard_normal(int(sec * SR))

def save(name, x, gain=0.8):
    x = x / (np.max(np.abs(x)) + 1e-9) * gain
    fd, tmp = tempfile.mkstemp(suffix=".wav"); os.close(fd)
    wavfile.write(tmp, SR, (x * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libvorbis", "-q:a", "4",
                    os.path.join(OUT, name + ".ogg")], check=True)
    os.remove(tmp)

# a card laid on the strip: a soft paper tap with a short slide
def card():
    n = noise(0.18); x = bp(n, 900, 5000) * env(len(n), 0.002, 0.03)
    s = bp(noise(0.18), 2000, 7000) * env(len(n), 0.01, 0.06) * 0.3
    thump = np.sin(2 * np.pi * 140 * np.arange(len(n)) / SR) * env(len(n), 0.001, 0.02) * 0.5
    return x + s + thump

def card_lift():
    n = noise(0.14); return bp(n, 1500, 6000) * env(len(n), 0.02, 0.04)

# a quill scratching a few strokes
def pen(strokes=5, sec=1.1):
    n = noise(sec); out = np.zeros_like(n); t = np.arange(len(n)) / SR
    for i in range(strokes):
        c = 0.08 + i * (sec - 0.2) / strokes + rng.uniform(-0.03, 0.03)
        w = np.exp(-((t - c) / 0.05) ** 2)
        out += w * (0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(18, 30) * t))
    return bp(n, 2500, 9000) * out * 0.6

def pen_short():
    return pen(2, 0.35)

# the seal pressed on: low thud + wax click
def stamp():
    n = int(0.45 * SR); t = np.arange(n) / SR
    thud = np.sin(2 * np.pi * (90 - 40 * t) * t) * env(n, 0.002, 0.08)
    click = bp(noise(0.45), 1200, 4000) * env(n, 0.001, 0.015) * 0.6
    return thud + click

# a page turned / a sheet arriving
def page(sec=0.55):
    n = noise(sec); t = np.arange(len(n)) / SR
    shape = np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 1.5
    crinkle = (rng.random(len(n)) < 0.004) * rng.standard_normal(len(n)) * 3
    return bp(n + crinkle, 800, 7000) * shape

def error():
    n = int(0.25 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 180 * t) + 0.5 * np.sin(2 * np.pi * 120 * t)) * env(n, 0.003, 0.07)

# a soft bell for a chronicle line / era change
def bell():
    n = int(2.2 * SR); t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in [(392, 1, .9), (784, .5, .6), (1176, .25, .35), (987, .2, .5)])
    return x * np.minimum(t / 0.004, 1)

# a quiet room: low air, distant wind, an occasional crackle of the brazier; loops
def room(sec=24.0):
    n = noise(sec); x = lp(n, 300) * 0.5 + bp(noise(sec), 300, 1200) * 0.08
    t = np.arange(len(n)) / SR
    x *= 0.75 + 0.25 * np.sin(2 * np.pi * t / sec * 3)
    for _ in range(40):
        p = int(rng.uniform(0.2, sec - 0.2) * SR)
        k = bp(noise(0.05), 1500, 6000) * env(int(0.05 * SR), 0.0005, 0.006) * rng.uniform(0.2, 0.7)
        x[p:p + len(k)] += k
    fade = int(0.5 * SR)  # crossfade the ends so the loop has no seam
    x[:fade] = x[:fade] * np.linspace(0, 1, fade) + x[-fade:] * np.linspace(1, 0, fade)
    return x[:-fade]

os.makedirs(OUT, exist_ok=True)
save("kart", card(), 0.6); save("kart_al", card_lift(), 0.4)
save("kalem", pen(), 0.45); save("kalem_kisa", pen_short(), 0.4)
save("muhur", stamp(), 0.8); save("sayfa", page(), 0.45); save("kagit", page(0.8), 0.35)
save("hata", error(), 0.35); save("can", bell(), 0.35); save("oda", room(), 0.25)
print("ok", sorted(os.listdir(OUT)))
