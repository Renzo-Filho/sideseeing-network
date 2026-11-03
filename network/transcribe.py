"""Transcribe a MultiSensor capture's audio on this machine with Whisper, with word timestamps.

Needs torch, transformers, soundfile and imageio-ffmpeg, which the sideseeing-tools venv has:
    ../sideseeing-tools/venv/bin/python network/transcribe.py data/pilot2/<session> [language] [model]
language defaults to portuguese, model to openai/whisper-large-v3-turbo (multilingual).

Writes data/<collection>_derived/<session>/audio16k.wav and words.csv (start_s, end_s, word).
Times are seconds from the start of video.mp4. Raw audio never leaves this machine.
"""
import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import pandas as pd
import soundfile as sf
from transformers import pipeline

session = Path(sys.argv[1]).resolve()
language = sys.argv[2] if len(sys.argv) > 2 else 'portuguese'
model = sys.argv[3] if len(sys.argv) > 3 else 'openai/whisper-large-v3-turbo'
out = session.parent.with_name(session.parent.name + '_derived') / session.name
out.mkdir(parents=True, exist_ok=True)

wav = out / 'audio16k.wav'
if not wav.exists():  # mono 16 kHz, what Whisper expects
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-i', str(session / 'video.mp4'),
                    '-vn', '-ac', '1', '-ar', '16000', str(wav)], check=True)

audio, rate = sf.read(wav, dtype='float32')
asr = pipeline('automatic-speech-recognition', model=model, device='cpu')

# 30 s windows every 28 s, one at a time so memory stays bounded. A word belongs to the window where it
# starts before second 29; the next window skips words starting in its first second (the shared overlap).
WIN, HOP = 30, 28
rows = []
n = math.ceil(len(audio) / rate / HOP)
for k in range(n):
    a = k * HOP
    clip = audio[int(a * rate):int((a + WIN) * rate)]
    r = asr({'raw': clip, 'sampling_rate': rate}, return_timestamps='word',
            generate_kwargs={'language': language, 'task': 'transcribe'})
    for c in r['chunks']:
        s0, s1 = c['timestamp']
        if s0 is None or (k > 0 and s0 < 1) or (k < n - 1 and s0 >= HOP + 1):
            continue
        rows.append((a + s0, a + (s1 if s1 is not None else s0), c['text'].strip()))
    print(f'window {k + 1}/{n}', flush=True)

words = pd.DataFrame(rows, columns=['start_s', 'end_s', 'word'])
words.to_csv(out / 'words.csv', index=False)
print(f'{len(words)} words from {len(audio) / rate / 60:.1f} min of {language} audio with {model} -> {out / "words.csv"}')
