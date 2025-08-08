import time
import os
from pathlib import Path
from typing import Union

import pyttsx3


def preload_tts_model():
    """Explicitly preload the TTS model.

    This is primarily exposed so FastAPI can trigger model loading in a
    startup event. The function is idempotent – repeated calls are no-ops
    after the first successful load.
    """
    # pyttsx3 doesn't require preloading, but we keep the interface consistent
    return None


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

    # Initialize pyttsx3 engine
    engine = pyttsx3.init()
    
    # Configure voice if specified
    if voice:
        voices = engine.getProperty('voices')
        for v in voices:
            if voice.lower() in v.name.lower() or voice.lower() in v.id.lower():
                engine.setProperty('voice', v.id)
                break
    
    # Set properties for better quality
    engine.setProperty('rate', 150)    # Speed of speech
    engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
    
    # Run inference
    begin = time.time()
    engine.save_to_file(text, out_path)
    engine.runAndWait()
    inference_time = time.time() - begin

    print(f"[TTS pyttsx3] Wrote {out_path} in {inference_time:.2f}s")
    return Path(out_path)
