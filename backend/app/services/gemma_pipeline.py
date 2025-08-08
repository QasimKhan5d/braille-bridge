"""
Shared Gemma pipeline service for both image and audio processing.
"""

import json
import os
from pathlib import Path
from typing import Optional, Tuple

import torch
from transformers import pipeline

# Global pipeline instance
_gemma_pipeline = None


def load_gemma_pipeline():
    """Load the Gemma pipeline once and cache it in memory.
    
    Returns
    -------
    pipeline
        The loaded Gemma pipeline for image-text-to-text processing.
    """
    global _gemma_pipeline
    
    if _gemma_pipeline is not None:
        return _gemma_pipeline
    
    print("Loading Gemma pipeline...")
    
    # Get Hugging Face token from environment
    hf_token = os.getenv("HUGGING_FACE_HUB_TOKEN")
    
    _gemma_pipeline = pipeline(
        "image-text-to-text",
        model="google/gemma-3n-e4b-it",
        device="cpu",
        torch_dtype=torch.bfloat16,
        token=hf_token,
    )
    print("Gemma pipeline loaded successfully")
    
    return _gemma_pipeline


def preload_gemma_pipeline():
    """Explicitly preload the Gemma pipeline.
    
    This is primarily exposed so FastAPI can trigger pipeline loading in a
    startup event. The function is idempotent – repeated calls are no-ops
    after the first successful load.
    """
    return load_gemma_pipeline()


async def process_image_with_gemma(image_path: Path, instruction: str) -> str:
    """Process an image with the Gemma pipeline.
    
    Parameters
    ----------
    image_path : Path
        Path to the image file.
    instruction : str
        Text instruction for the model.
        
    Returns
    -------
    str
        The generated text response.
    """
    pipeline = load_gemma_pipeline()
    if pipeline is None:
        raise RuntimeError("Gemma pipeline not loaded")
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": str(image_path)},
                {"type": "text", "text": instruction},
            ],
        }
    ]
    
    output = pipeline(messages, max_new_tokens=2048)
    result = output[0]["generated_text"][-1]["content"]
    return result



async def process_audio_with_gemma(audio_path: str, question: Optional[str] = None) -> Tuple[str, str]:
    """Process audio with the Gemma pipeline.
    
    Parameters
    ----------
    audio_path : str
        Path to the audio file.
    question : Optional[str]
        Optional question context for better translation.
        
    Returns
    -------
    Tuple[str, str]
        Tuple of (urdu_text, english_text).
    """
    pipeline = load_gemma_pipeline()
    if pipeline is None:
        raise RuntimeError("Gemma pipeline not loaded")
    
    # Prepare instruction for Gemma
    if question:
        instruction = f"""This audio is a student's answer to the following question: "{question}"

Translate the audio to both Urdu and English, keeping the question context in mind for accurate translation. Your response should be in the following format:
```json
{{
    "english": "...",
    "urdu": "..."
}}
```
"""
    else:
        instruction = """Translate the following audio to both Urdu and English. Your response should be in the following format:
```json
{
    "english": "...",
    "urdu": "..."
}
```
"""

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "audio", "audio": audio_path},
                {"type": "text", "text": instruction},
            ],
        }
    ]
    
    try:
        output = pipeline(messages, max_new_tokens=1024)
        result = output[0]["generated_text"][-1]["content"]
        
        # Parse JSON response
        try:
            # Extract JSON from response
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = result[json_start:json_end]
                parsed = json.loads(json_str)
                urdu_text = parsed.get("urdu", "").strip()
                english_text = parsed.get("english", "").strip()
                return urdu_text, english_text
            else:
                return "Audio processing failed", "Audio processing failed"
        except json.JSONDecodeError:
            return "Audio parsing failed", "Audio parsing failed"
            
    except Exception as e:
        print(f"Error processing audio with Gemma: {e}")
        return "Audio processing failed", "Audio processing failed"
