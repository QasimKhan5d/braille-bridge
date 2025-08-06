import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import json
from pathlib import Path
from typing import List, Tuple, Optional
import louis
from fastapi.responses import FileResponse, StreamingResponse
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from lesson_pack_service import generate_lesson_pack

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    import tts_service
    tts_service.preload_tts_model()
    # Load Gemma audio processing model
    await load_gemma_audio_model()
    yield
from yolo_to_text import YOLOBrailleReader
import asyncio


app = FastAPI(
    title="BrailleBridge Teacher API",
    description="API for processing braille images and converting to Urdu text",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize YOLO reader
model_path = Path(__file__).parent / "yolo11n.pt"
if not model_path.exists():
    print(f"Warning: Model not found at {model_path}")
    reader = None
else:
    reader = YOLOBrailleReader(str(model_path), confidence_threshold=0.3)

# Global variables for Gemma audio model
gemma_processor = None
gemma_model = None

async def load_gemma_audio_model():
    """Load Gemma audio processing model once at startup"""
    global gemma_processor, gemma_model
    try:
        from transformers import AutoProcessor, AutoModelForImageTextToText
        PRETRAINED_MODEL = "google/gemma-3n-E4B-it"
        gemma_processor = AutoProcessor.from_pretrained(PRETRAINED_MODEL)
        gemma_model = AutoModelForImageTextToText.from_pretrained(PRETRAINED_MODEL)
        print("Gemma audio model loaded successfully")
    except Exception as e:
        print(f"Failed to load Gemma audio model: {e}")
        gemma_processor = None
        gemma_model = None

async def process_audio_with_gemma(audio_path: str, question: str = None) -> tuple[str, str]:
    """Process audio file and return (urdu_text, english_text)"""
    import librosa
    import soundfile as sf
    import numpy as np
    import tempfile
    import json
    
    if not gemma_processor or not gemma_model:
        raise Exception("Gemma audio model not loaded")
    
    # Preprocess audio (based on gemma_audio_processing.py)
    audio, sr = librosa.load(audio_path, sr=None)
    
    # Convert to mono if stereo
    if len(audio.shape) > 1:
        audio = librosa.to_mono(audio)
    
    # Resample to 16kHz if needed
    if sr != 16000:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
        sr = 16000
    
    # Limit duration to 30 seconds
    max_samples = int(sr * 30)
    if len(audio) > max_samples:
        audio = audio[:max_samples]
    
    # Ensure float32 and normalize
    audio = audio.astype(np.float32)
    max_val = np.max(np.abs(audio))
    if max_val > 1.0:
        audio = audio / max_val
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        sf.write(temp_file.name, audio, 16000, subtype="FLOAT")
        temp_audio_path = temp_file.name
    
    try:
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
                    {"type": "audio", "audio": temp_audio_path},
                    {"type": "text", "text": instruction}
                ]
            }
        ]
        
        inputs = gemma_processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt"
        )
        inputs = inputs.to(gemma_model.device, dtype=gemma_model.dtype)
        
        outputs = gemma_model.generate(**inputs, max_new_tokens=1024)
        result = gemma_processor.decode(outputs[0][inputs["input_ids"].shape[-1]:])
        
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
    
    finally:
        # Clean up temp file
        import os
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

@app.get("/")
async def root():
    return {"message": "BrailleBridge Teacher API"}

@app.post("/api/process-braille")
async def process_braille_image(file: UploadFile = File(...)):
    """
    Process a braille image and return both Urdu and Braille text.
    """
    if not reader:
        raise HTTPException(status_code=500, detail="YOLO model not loaded")
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Process image
        braille_lines, urdu_lines = reader.predict_and_decode(tmp_file_path)
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        # Join lines
        braille_text = "\n".join(braille_lines)
        urdu_text = "\n".join(urdu_lines)
        
        return {
            "braille_text": braille_text,
            "urdu_text": urdu_text,
            "braille_lines": braille_lines,
            "urdu_lines": urdu_lines,
            "errors": []  # TODO: Implement error detection
        }
        
    except Exception as e:
        # Clean up temp file if it exists
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

from progress_bus import register_listener, remove_listener  # after imports above


@app.get("/api/progress-stream")
async def progress_stream():
    """Stream structured progress events for lesson pack generation."""
    q = register_listener()

    async def event_generator():
        try:
            while True:
                event = await q.get()
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            remove_listener(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/lesson-pack")
async def create_lesson_pack(
    files: List[UploadFile] = File(...),
    prompts: str = File(...),
    title: str = Form("lesson_pack"),
    assignment_id: str | None = Form(None)
):
    """files: images, prompts: JSON list matching files order"""
    
    prompt_list = json.loads(prompts)
    if len(prompt_list) != len(files):
        raise HTTPException(status_code=400, detail="files and prompts length mismatch")

    temp_dir = Path(tempfile.mkdtemp())
    saved_paths: List[Tuple[Path, str]] = []
    for f, p in zip(files, prompt_list):
        if not f.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="all files must be images")
        dest = temp_dir / f.filename
        with dest.open("wb") as out:
            out.write(await f.read())
        saved_paths.append((dest, p))

    aid_int = int(assignment_id) if assignment_id and assignment_id.isdigit() else None
    zip_path = await generate_lesson_pack(saved_paths, aid_int)
    import re
    safe_title = re.sub(r"[^A-Za-z0-9_-]+", "_", title.strip()) or "lesson_pack"
    return FileResponse(zip_path, filename=f"{safe_title}.zip")


@app.post("/api/text-to-braille")
async def text_to_braille(payload: dict):
    """Convert plain text to Grade-1 Braille depending on language."""
    text = payload.get("text", "").strip()
    lang = payload.get("lang", "urdu").lower()
    if not text:
        raise HTTPException(status_code=400, detail="text required")

    if lang not in ("urdu", "english"):
        raise HTTPException(status_code=400, detail="lang must be 'urdu' or 'english'")

    table = "ur-pk-g1.utb" if lang == "urdu" else "en-ueb-g1.ctb"
    braille = louis.translateString(["braille-patterns.cti", table], text)
    # strip newlines & excessive whitespace while preserving real spaces
    braille_clean = " ".join(braille.splitlines())
    return {"braille_text": braille_clean}


# New endpoint: Urdu to English translation using Ollama LLM
@app.post("/api/translate-urdu-english")
async def translate_urdu_to_english(payload: dict):
    """Translate provided Urdu text to English using a local LLM (Gemma3n via Ollama)."""
    import asyncio
    
    from ollama import chat  # type: ignore

    text = payload.get("text", "").strip()
    question = payload.get("question", "").strip()  # Optional question context
    if not text:
        raise HTTPException(status_code=400, detail="text required")

    def _call_llm(urdu: str, question_context: str = "") -> str:
        if question_context:
            prompt = f"This is a student's answer to the question: '{question_context}'\n\nTranslate the following Urdu text to English, keeping the question context in mind:\n\n{urdu}\n\nProvide only the translated English sentence(s) without additional commentary. Do not include any text not mentioned in the student's answer."
        else:
            prompt = f"Translate the following Urdu text to English:\n\n{urdu}\n\nProvide only the translated English sentence(s) without additional commentary."
        response = chat(model="gemma3n:e2b", messages=[{"role": "user", "content": prompt}])
        return response.message.content.strip()

    try:
        english_text: str = await asyncio.to_thread(_call_llm, text, question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"translation error: {e}")

    return {"english_text": english_text}

# Internal helper used by server-side functions
async def translate_urdu_to_english_internal(text: str) -> str:
    payload = {"text": text}
    return (await translate_urdu_to_english(payload))["english_text"]


# ---------------------------------------------------------------------------
# ASSIGNMENT CRUD
# ---------------------------------------------------------------------------
from db import insert_assignment, get_assignment, all_assignments, insert_submission, get_submission, all_submissions, submissions_table, db, add_student_feedback, get_all_students  # type: ignore

UPLOADS_DIR = (Path(__file__).parent / "uploads").resolve()
from fastapi.staticfiles import StaticFiles
UPLOADS_DIR.mkdir(exist_ok=True)
# Serve uploaded files statically so the frontend can access them
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

@app.post("/api/assignments")
async def create_assignment(
    files: List[UploadFile] = File(...),
    prompts: str = File(...),
    title: str = Form("assignment"),
    contexts: str | None = Form(None),
):
    """Save assignment diagrams (images) + prompts and return assignment id."""
    prompt_list = json.loads(prompts)
    if len(prompt_list) != len(files):
        raise HTTPException(status_code=400, detail="files and prompts length mismatch")

    context_list = json.loads(contexts) if contexts else [None] * len(files)
    if len(context_list) != len(files):
        raise HTTPException(status_code=400, detail="contexts length mismatch")

    diagrams_meta: List[dict] = []
    for idx, (f, p, ctx) in enumerate(zip(files, prompt_list, context_list)):
        if not f.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="all files must be images")
        filename = f"assign_{title}_{idx}_{f.filename}"
        dest_path = UPLOADS_DIR / filename
        with dest_path.open("wb") as out:
            out.write(await f.read())
        diagrams_meta.append({"image_path": str(dest_path.relative_to(Path(__file__).parent)), "prompt": p, "context": ctx or p})

    assignment_id = insert_assignment(title, diagrams_meta)
    return {"assignment_id": assignment_id}


@app.get("/api/assignments")
async def list_assignments():
    return all_assignments()


@app.get("/api/assignments/{assignment_id}")
async def get_assignment_details(assignment_id: int):
    assignment = get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="assignment not found")
    return assignment


# ---------------------------------------------------------------------------
# EXTERNAL SUBMISSION CREATION (JSON)
# ---------------------------------------------------------------------------
@app.post("/api/external-submissions")
async def create_external_submission(payload: dict):
    """Endpoint for external systems to create a submission without uploading files.

    Expected payload:
    {
        "assignment_id": int,
        "student": "name",
        "answers": [ {"diagram_idx": int, "answer_type": "image"|"audio", "file_path": str} ]
    }
    """
    assignment_id = payload.get("assignment_id")
    student = payload.get("student", "").strip()
    answers = payload.get("answers", [])

    if not assignment_id or not student or not answers:
        raise HTTPException(status_code=400, detail="assignment_id, student, answers required")

    # ensure assignment exists
    if not get_assignment(assignment_id):
        raise HTTPException(status_code=404, detail="assignment not found")

    # validate answers minimal fields
    for a in answers:
        if not all(k in a for k in ("diagram_idx", "answer_type", "file_path")):
            raise HTTPException(status_code=400, detail="answers must have diagram_idx, answer_type, file_path")
        a.setdefault("urdu_text", "")
        a.setdefault("english_text", "")
        a.setdefault("braille_text", None)
        a.setdefault("errors", [])

    sub_id = insert_submission(assignment_id, student, answers)
    return {"submission_id": sub_id}

# ---------------------------------------------------------------------------
# SUBMISSIONS
# ---------------------------------------------------------------------------
@app.post("/api/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    student: str = Form(...),
    answer_type: str = Form("image"),  # 'image' or 'audio'
    file: UploadFile = File(...),
):
    assignment = get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="assignment not found")

    if answer_type not in ("image", "audio"):
        raise HTTPException(status_code=400, detail="answer_type must be 'image' or 'audio'")

    # Save file
    dest_name = f"sub_{assignment_id}_{student}_{file.filename}"
    dest_path = UPLOADS_DIR / dest_name
    with dest_path.open("wb") as out:
        out.write(await file.read())

    # Get question context for better translation
    diagram_meta = assignment["diagrams"][0]  # using diagram_idx 0 for now
    question = diagram_meta["prompt"]

    # Process depending on type
    if answer_type == "image":
        if not reader:
            raise HTTPException(status_code=500, detail="YOLO model not loaded")
        braille_lines, urdu_lines = reader.predict_and_decode(str(dest_path))
        braille_text = "\n".join(braille_lines)
        urdu_text = "\n".join(urdu_lines)
        english_text = ""  # can translate later
    else:  # audio processing
        braille_text = None
        urdu_text, english_text = await process_audio_with_gemma(str(dest_path), question)

    answers = [
        {
            "diagram_idx": 0,  # keep simple for now
            "answer_type": answer_type,
            "file_path": str(dest_path.relative_to(Path(__file__).parent)),
            "urdu_text": urdu_text,
            "braille_text": braille_text,
            "english_text": english_text,
            "errors": [],
        }
    ]

    sub_id = insert_submission(assignment_id, student, answers)
    return {"submission_id": sub_id}


@app.get("/api/submissions")
async def list_submissions():
    return all_submissions()


@app.post("/api/submissions/{submission_id}/autograde")
async def autograde_submission(submission_id: int, answer_index: int = 0):
    sub = get_submission(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="submission not found")

    from pydantic import BaseModel
    from ollama import chat  # type: ignore

    class GradeResult(BaseModel):
        correct: bool
        explanation: str
        error_start: int | None = None
        error_end: int | None = None

    # Validate answer_index
    if answer_index < 0 or answer_index >= len(sub["answers"]):
        raise HTTPException(status_code=400, detail=f"Invalid answer_index {answer_index}. Submission has {len(sub['answers'])} answers.")

    ans = sub["answers"][answer_index]
    assignment = get_assignment(sub["assignment_id"])
    diagram_meta = assignment["diagrams"][ans["diagram_idx"]]
    question = diagram_meta["prompt"]
    diagram_json = diagram_meta["context"]
    
    # Single LLM call for grading and error location
    is_image = ans["answer_type"] == "image"
    
    if is_image:
        grade_prompt = (
            "You are grading a student's answer. Use ONLY the diagram JSON as factual context."\
            "\n\nQuestion: " + question + "\n\n"\
            f"Diagram context (JSON):\n{diagram_json}\n\n"\
            f"Student answer:\n{ans['english_text']}\n\n"\
            f"Original Urdu text:\n{ans['urdu_text']}\n\n"\
            "Respond with a JSON object containing:\n"\
            "- 'correct' (boolean): whether the answer is correct\n"\
            "- 'explanation' (string): 1-2 sentence explanation\n"\
            "- 'error_start' (int or null): if incorrect, start character position of error in Urdu text\n"\
            "- 'error_end' (int or null): if incorrect, end character position of error in Urdu text\n"\
            "For error positions, pinpoint the specific word or phrase rather than the entire sentence."
        )
    else:
        grade_prompt = (
            "You are grading a student's answer. Use ONLY the diagram JSON as factual context."\
            "\n\nQuestion: " + question + "\n\n"\
            f"Diagram context (JSON):\n{diagram_json}\n\n"\
            f"Student answer:\n{ans['english_text']}\n\n"\
            "Respond with a JSON object containing 'correct' (boolean) and 'explanation' (string)."
        )
    
    grade_schema = GradeResult.model_json_schema()
    grade_response = chat(model="gemma3n:e2b", messages=[{"role": "user", "content": grade_prompt}], format=grade_schema)
    grade_result = GradeResult.model_validate_json(grade_response.message.content)
    
    return {
        "correct": grade_result.correct,
        "explanation": grade_result.explanation,
        "error_start": grade_result.error_start,
        "error_end": grade_result.error_end
    }


@app.get("/api/submissions/{submission_id}")
async def get_submission_details(submission_id: int):
    """Fetch submission and, if text fields are missing, automatically compute them."""
    sub = get_submission(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="submission not found")

    # Get assignment context for translation
    assignment = get_assignment(sub["assignment_id"])
    if not assignment:
        raise HTTPException(status_code=404, detail="assignment not found")

    updated_needed = False

    for ans in sub["answers"]:
        # Only process if urdu_text is missing or empty
        if ans.get("urdu_text"):
            continue
        if ans["answer_type"] == "image":
            # Fix file path - remove 'backend/' prefix if present
            file_path = ans["file_path"].replace("backend/", "", 1)
            img_path = Path(__file__).parent / file_path
            if not img_path.exists():
                continue  # can't process
            # Run YOLO OCR
            if not reader:
                continue
            braille_lines, urdu_lines = reader.predict_and_decode(str(img_path))
            ans["braille_text"] = "\n".join(braille_lines)
            raw_urdu = "\n".join(urdu_lines)

            # Get the original question for context
            diagram_meta = assignment["diagrams"][ans["diagram_idx"]]
            question = diagram_meta["prompt"]

            # --- Validate & translate Urdu via Gemma ---
            from pydantic import BaseModel
            from ollama import chat

            class UrduEnglishCorrection(BaseModel):
                urdu_text: str
                english_text: str

            schema = UrduEnglishCorrection.model_json_schema()
            prompt = (
                "The following Urdu text may contain OCR errors or mangled words. "
                "This is a student's answer to a specific question. Use the question context to help correct and translate the text.\n\n"
                f"Original Question: {question}\n\n"
                "If the text is completely incoherent, just write N/A. "
                "If it is just incoherent, rewrite it to be coherent while staying " 
                "faithful to the student's original answer and considering the question context. "
                "If it is both coherent and comprehensible, return the original text. "
                "Then provide an English translation that makes sense in the context of the question. "
                "Do not add any other text except the translations.\n\n"
                f"Student's Urdu Text:\n{raw_urdu}\n\n"
                "Respond ONLY with a JSON object that matches this schema."
            )
            response = chat(model="gemma3n:e2b", messages=[{"role": "user", "content": prompt}], format=schema)
            content = response.message.content
            try:
                parsed = UrduEnglishCorrection.model_validate_json(content)
                ans["urdu_text"] = parsed.urdu_text.strip()
                ans["english_text"] = parsed.english_text.strip()
            except Exception as e:
                print(f"Error parsing JSON: {content}")
                ans["urdu_text"] = raw_urdu
                ans["english_text"] = ""
            ans["errors"] = []
            updated_needed = True
        else:  # audio processing
            # Fix file path - remove 'backend/' prefix if present
            file_path = ans["file_path"].replace("backend/", "", 1)
            audio_path = Path(__file__).parent / file_path
            if not audio_path.exists():
                continue
            
            # Get the original question for context
            diagram_meta = assignment["diagrams"][ans["diagram_idx"]]
            question = diagram_meta["prompt"]
            
            urdu_text, english_text = await process_audio_with_gemma(str(audio_path), question)
            ans["urdu_text"] = urdu_text
            ans["english_text"] = english_text
            ans["braille_text"] = None
            ans["errors"] = []
            updated_needed = True

    if updated_needed:
        # Persist updates
        submissions_table.update({"answers": sub["answers"]}, doc_ids=[submission_id])
        db.storage.flush()

    # attach assignment for convenience
    sub["assignment"] = get_assignment(sub["assignment_id"])
    return sub


@app.post("/api/feedback/analyze")
async def analyze_feedback_for_student(payload: dict):
    """Analyze feedback and generate strength/weakness for student profile"""
    from pydantic import BaseModel
    from ollama import chat  # type: ignore
    
    class StudentFeedback(BaseModel):
        trait: str  # max 3 words describing strength or weakness
    
    feedback_text = payload.get("feedback", "").strip()
    is_correct = payload.get("is_correct", False)
    student_name = payload.get("student_name", "").strip()
    
    if not feedback_text or not student_name:
        raise HTTPException(status_code=400, detail="feedback and student_name required")
    
    trait_type = "strength" if is_correct else "weakness"
    
    prompt = (
        f"Based on this teacher feedback about a student's answer, generate a single 1-3 word trait "
        f"that describes the student's {trait_type}. Use language a teacher would use in a student profile. "
        f"Be specific and educational.\n\n"
        f"Feedback: {feedback_text}\n\n"
        f"Respond with a JSON object containing 'trait' (1-3 words max)."
    )
    
    schema = StudentFeedback.model_json_schema()
    response = chat(model="gemma3n:e2b", messages=[{"role": "user", "content": prompt}], format=schema)
    parsed = StudentFeedback.model_validate_json(response.message.content)
    
    # Save to student profile
    feedback_type = "strength" if is_correct else "challenge"
    add_student_feedback(student_name, feedback_type, parsed.trait)
    
    return {"trait": parsed.trait, "type": feedback_type}


@app.get("/api/students")
async def get_students():
    """Get all student profiles with strengths and challenges"""
    return get_all_students()


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "model_loaded": reader is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 