import json
import tempfile
from pathlib import Path
from typing import List, Tuple
import zipfile
import shutil

import louis
import logging
import asyncio
from fastapi import HTTPException

from transformers import AutoProcessor, AutoModelForImageTextToText
from ollama import AsyncClient

# --- Load heavy models at module import ------------------------------

HF_MODEL_ID = "cookiefinder/gemma-3N-finetune" 
TTS_SCRIPT = Path(__file__).parent / "tts_mlx.py"

_hf_processor = AutoProcessor.from_pretrained(HF_MODEL_ID)
_hf_model = AutoModelForImageTextToText.from_pretrained(HF_MODEL_ID)

_ollama_client = AsyncClient()

# --------------------------------------------------------------------
# Logger setup
# --------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# --------------------------------------------------------------------

async def _diagram_json_from_image(image_path: Path) -> dict:
    if not (_hf_model and _hf_processor):
        raise HTTPException(status_code=500, detail="HF diagram model not loaded")
    
    instruction = Path("diagram2json.txt").read_text()
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "url": str(image_path)},
                {"type": "text", "text": instruction},
            ],
        }
    ]
    # For simplicity, just call model.generate on captioning style
    inputs = _hf_processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    ).to(_hf_model.device)

    output_ids = _hf_model.generate(**inputs, max_new_tokens=2048)
    raw = _hf_processor.decode(output_ids[0][inputs["input_ids"].shape[-1]:])

    try:
        # Remove any trailing special tokens (like <end_of_turn>) and whitespace before parsing
        cleaned = raw.strip()
        if cleaned.endswith("<end_of_turn>"):
            cleaned = cleaned[: cleaned.rfind("<end_of_turn>")].strip()
        # Optionally, try to extract the JSON block if it's surrounded by ```json ... ```
        if "```json" in cleaned:
            start = cleaned.find("```json") + len("```json")
            end = cleaned.find("```", start)
            if end != -1:
                cleaned = cleaned[start:end].strip()
        data = json.loads(cleaned)
    except Exception:
        print("Warning: Failed to parse JSON from model output")
        print("Raw output:", raw)
        data = {"raw": raw}
    return data


async def _english_and_urdu_scripts(diagram_json: dict) -> Tuple[str, str]:
    if not _ollama_client:
        raise HTTPException(status_code=500, detail="Ollama client not available")

    json_str = json.dumps(diagram_json, ensure_ascii=False, indent=2)
    script_prompt = Path( "json2script.txt").read_text()

    english_prompt = f"{script_prompt}\n\nHere is the JSON:\n```json\n{json_str}\n```"

    english_resp = await _ollama_client.chat(
        model="gemma3n:e2b",
        messages=[{"role": "user", "content": english_prompt}],
    )
    english_script = english_resp['message']['content'].strip()

    urdu_prompt = (
        "Translate the following narration script into simple, child friendly Urdu "
        "while keeping the meaning intact. Output only the Urdu text.\n\n"
        + english_script
    )
    urdu_resp = await _ollama_client.chat(
        model="gemma3n:e2b",
        messages=[{"role": "user", "content": urdu_prompt}],
    )
    urdu_script = urdu_resp['message']['content'].strip()
    return english_script, urdu_script


def _text_to_braille(text: str, lang: str) -> str:
    table = "ur-pk-g1.utb" if lang == "urdu" else "en-ueb-g1.ctb"
    braille = louis.translateString(["braille-patterns.cti", table], text)
    return " ".join(braille.splitlines())


def _braille_to_svg(braille_text: str, out_path: Path, cols: int = 24):
    """Render braille text to an SVG file with fixed column wrapping.

    Each row contains at most *cols* characters (default 24).
    """
    # Split text into rows of `cols` characters
    lines = [braille_text[i : i + cols] for i in range(0, len(braille_text), cols)]

    char_width = 16  # fits SimBraille nicely at font-size 32
    line_height = 40  # vertical distance between baselines

    svg_width = cols * char_width
    svg_height = 48 + max(0, len(lines) - 1) * line_height

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}">'
    ]

    for row_idx, line in enumerate(lines):
        y = 32 + row_idx * line_height  # baseline position
        parts.append(
            f'<text x="0" y="{y}" font-family="SimBraille, sans-serif" font-size="32">{line}</text>'
        )

    parts.append("</svg>")
    out_path.write_text("".join(parts), encoding="utf-8")


async def generate_lesson_pack(pairs: List[Tuple[Path, str]], assignment_id: int | None = None) -> Path:
    """Generate a zipped lesson pack and return the zip path.

    Logging at INFO level provides progress feedback in the server logs.
    """
    from progress_bus import push as emit_progress

    total = len(pairs)
    emit_progress({"status": "starting", "total": total})
    logger.info("Starting lesson pack generation (%d items)", total)
    """pairs = [(image_path, question_prompt), ...]"""
    tmpdir = Path(tempfile.mkdtemp())

    for idx, (img_path, prompt) in enumerate(pairs, start=1):
        emit_progress({"status": "processing", "idx": idx, "total": total, "filename": img_path.name})
        logger.info("[%d/%d] Processing image: %s", idx, total, img_path.name)
        await asyncio.sleep(0)
        item_dir = tmpdir / f"item_{idx}"
        item_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(img_path, item_dir / img_path.name)
        (item_dir / "question.txt").write_text(prompt, encoding="utf-8")

        logger.info("[%d/%d] Extracting diagram data", idx, len(pairs))
        await asyncio.sleep(0)
        diagram_json = await _diagram_json_from_image(img_path)
        emit_progress({"status": "diagram_ready", "idx": idx, "total": total})
        logger.info("[%d/%d] Diagram JSON ready", idx, total)
        (item_dir / "diagram.json").write_text(json.dumps(diagram_json, ensure_ascii=False, indent=2))
        if assignment_id is not None:
            from db import set_diagram_context
            set_diagram_context(assignment_id, idx - 1, json.dumps(diagram_json, ensure_ascii=False))

        logger.info("[%d/%d] Generating narration scripts", idx, len(pairs))
        await asyncio.sleep(0)
        eng_script, urd_script = await _english_and_urdu_scripts(diagram_json)
        emit_progress({"status": "scripts_ready", "idx": idx, "total": total})
        logger.info("[%d/%d] Scripts generated", idx, total)
        (item_dir / "script_en.txt").write_text(eng_script, encoding="utf-8")
        (item_dir / "script_ur.txt").write_text(urd_script, encoding="utf-8")

        emit_progress({"status": "braille_ready", "idx": idx, "total": total})
        logger.info("[%d/%d] Converting scripts to braille", idx, total)
        await asyncio.sleep(0)
        braille_en = _text_to_braille(eng_script, "english")
        braille_ur = _text_to_braille(urd_script, "urdu")
        (item_dir / "braille_en.txt").write_text(braille_en, encoding="utf-8")
        (item_dir / "braille_ur.txt").write_text(braille_ur, encoding="utf-8")

        _braille_to_svg(braille_en, item_dir / "braille_en.svg")
        _braille_to_svg(braille_ur, item_dir / "braille_ur.svg")

        emit_progress({"status": "audio_ready", "idx": idx, "total": total})
        logger.info("[%d/%d] Generating English audio via TTS", idx, total)
        await asyncio.sleep(0)
        # Generate English audio via TTS service
        from tts_service import synthesize 
        synthesize(eng_script, item_dir / "audio_en.wav")

    # Zip pack
    zip_path = tmpdir / "lesson_pack.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in tmpdir.rglob("*"):
            if file == zip_path:
                continue
            zf.write(file, file.relative_to(tmpdir))
    emit_progress({"status": "finished", "download": str(zip_path)})
    logger.info("Lesson pack ready: %s", zip_path)
    await asyncio.sleep(0)
    return zip_path
