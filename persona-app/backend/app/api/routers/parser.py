import os
import json
from fastapi import APIRouter,UploadFile, File


from app.services.parser.pptx_slide1 import parse_pptx
from app.services.parser.pptx_slide2 import parse_slide2

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

router = APIRouter(prefix="/parser", tags=["parser"])

@router.post("/parse")
async def parse(pptx: UploadFile = File(...)):
    # file save
    file_path = os.path.join(UPLOAD_DIR, pptx.filename)
    content = await pptx.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # parsing slide 1 (MVP)
    parsed_s1 = parse_pptx(file_path)
    parsed_s2 = parse_slide2(file_path)

    parsed = {
        "persona": parsed_s1,
        "journey": parsed_s2
    }

    return parsed

@router.post("/submit")
async def submit_payload(payload: dict):
    # saving the final JSON
    out_path = os.path.join(OUTPUT_DIR, "persona_submission.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return {"saved_to": out_path}