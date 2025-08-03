import os
import librosa
import soundfile as sf
import numpy as np
from transformers import AutoProcessor, AutoModelForImageTextToText

def preprocess_audio_for_gemma(audio_path, max_duration=30):
    """
    Preprocess audio to meet Gemma's requirements:
    - Single channel (mono)
    - 16kHz sample rate
    - Float32 bit depth in range [-1, 1]
    - Maximum 30 seconds duration
    """
    # Load audio file
    audio, sr = librosa.load(audio_path, sr=None)
    
    # Convert to mono if stereo
    if len(audio.shape) > 1:
        audio = librosa.to_mono(audio)
    
    # Resample to 16kHz if needed
    if sr != 16000:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
        sr = 16000
    
    # Limit duration to max_duration seconds
    max_samples = int(sr * max_duration)
    if len(audio) > max_samples:
        audio = audio[:max_samples]
        print(f"Audio trimmed to {max_duration} seconds")
    
    # Ensure float32 and normalize to [-1, 1] range
    audio = audio.astype(np.float32)
    
    # Normalize if needed (librosa already does this, but double-check)
    max_val = np.max(np.abs(audio))
    if max_val > 1.0:
        audio = audio / max_val
    
    # Save preprocessed audio to temporary file using the exact pattern from working code
    temp_audio_path = "temp_processed_audio.wav"
    sf.write(temp_audio_path, audio, 16000, subtype="FLOAT")
    
    duration_seconds = len(audio) / sr
    print(f"Audio duration: {duration_seconds:.2f}s")
    print("Audio path: ", temp_audio_path)
    return temp_audio_path


# Update instruction to include the model schema
instruction = f"""Translate the following audio to both Urdu and English. Your response should be in the following format:
```json
{{
    "english": "...",
    "urdu": "..."
}}
```
"""

# Load model
PRETRAINED_MODEL = "google/gemma-3n-E4B-it"
processor = AutoProcessor.from_pretrained(PRETRAINED_MODEL)
model = AutoModelForImageTextToText.from_pretrained(PRETRAINED_MODEL)

# Get project root directory for relative path
project_root = "/Users/qasim.khan/Documents/gemma3nImpactChallenge/braille-bridge"
audio_file = os.path.join(project_root, "cactus-eng.m4a")

# Preprocess audio for Gemma
processed_audio_path = preprocess_audio_for_gemma(audio_file)

messages = [
    {
        "role": "user",
        "content": [
            {"type": "audio", "audio": processed_audio_path},
            {"type": "text", "text": instruction}
        ]
    },
]
print("Messages:", messages)

try:
    inputs = processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt"
    )
    inputs = inputs.to(model.device, dtype=model.dtype)

    outputs = model.generate(**inputs, max_new_tokens=1024)
    result = processor.decode(outputs[0][inputs["input_ids"].shape[-1]:])
    print(result)

finally:
    # Clean up temporary file
    if os.path.exists(processed_audio_path):
        os.remove(processed_audio_path)