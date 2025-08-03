import queue
import time
from pathlib import Path
from typing import Union

import mlx.core as mx
import numpy as np
import sphn

# Reuse the shared loader from tts_mlx so we only pay model init cost once.
from tts_mlx import load_tts_model

# Lazily load the heavy model the first time this module is imported (or
# explicitly via `preload_tts_model`).
_tts_model, _mimi, _cfg_is_no_text, _cfg_is_no_prefix, _cfg_coef_conditioning = load_tts_model()


def preload_tts_model():
    """Explicitly preload the TTS model.

    This is primarily exposed so FastAPI can trigger model loading in a
    startup event. The function is idempotent – repeated calls are no-ops
    after the first successful load.
    """
    return _tts_model


def synthesize(text: str, out_path: Union[str, Path], *, voice: str | None = None):
    """Convert *text* to speech and write a WAV file to *out_path*.

    Parameters
    ----------
    text : str
        The text to synthesise.
    out_path : Union[str, pathlib.Path]
        Destination path for the generated WAV audio.
    voice : str, optional
        Override voice for multi-speaker models. When omitted the default
        voice bundled with the checkpoint is used.
    """
    if isinstance(out_path, Path):
        out_path = str(out_path)

    # Queue used to collect PCM frames from the callback.
    wav_frames: "queue.Queue[np.ndarray]" = queue.Queue()

    def _on_frame(frame):
        # Skip padding frames (all -1 values)
        if (frame == -1).any():
            return
        pcm = _mimi.decode_step(frame[:, :, None])
        pcm = np.array(mx.clip(pcm[0, 0], -1, 1))
        wav_frames.put_nowait(pcm)

    # Prepare inputs for the underlying model
    entries = [_tts_model.prepare_script([text])]

    if _tts_model.multi_speaker:
        chosen_voice = voice or "expresso/ex03-ex01_happy_001_channel1_334s.wav"
        voices = [_tts_model.get_voice_path(chosen_voice)]
    else:
        voices = []

    attributes = [_tts_model.make_condition_attributes(voices, _cfg_coef_conditioning)]

    # Run inference (blocking) – frames are streamed into the queue via the
    # on_frame callback.
    begin = time.time()
    _tts_model.generate(
        entries,
        attributes,
        cfg_is_no_prefix=_cfg_is_no_prefix,
        cfg_is_no_text=_cfg_is_no_text,
        on_frame=_on_frame,
    )
    inference_time = time.time() - begin

    # Gather the PCM data.
    frames = []
    while True:
        try:
            frames.append(wav_frames.get_nowait())
        except queue.Empty:
            break

    if not frames:
        raise RuntimeError("TTS generation produced no audio frames")

    wav = np.concatenate(frames, -1)
    sphn.write_wav(out_path, wav, _mimi.sample_rate)

    print(f"[TTS] Wrote {out_path} in {inference_time:.2f}s")
    return Path(out_path)
