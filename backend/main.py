from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import os
import random

app = FastAPI(title="Stock Quiz Game API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. JSON 데이터베이스 파일 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STAGE1_PATH = os.path.join(BASE_DIR, "stage1_quizzes.json")
STAGE2_PATH = os.path.join(BASE_DIR, "stage2_quizzes.json")
STAGE3_PATH = os.path.join(BASE_DIR, "stage3_quizzes.json")
CARDS_PATH = os.path.join(BASE_DIR, "cards.json")
ACHIEVEMENTS_PATH = os.path.join(BASE_DIR, "achievements.json")
REBIRTH_SHOP_PATH = os.path.join(BASE_DIR, "rebirth_shop.json")

STAGE_QUIZZES = {1: [], 2: [], 3: []}
QUIZ_DATABASE = []

def load_and_shuffle_quizzes(file_path: str, stage_num: int):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            for quiz in data:
                if "options" in quiz and "answer_index" in quiz and 0 <= quiz["answer_index"] < len(quiz["options"]):
                    correct_text = quiz["options"][quiz["answer_index"]]
                    random.shuffle(quiz["options"])
                    quiz["answer_index"] = quiz["options"].index(correct_text)
            return data
    except Exception as e:
        print(f"Stage {stage_num} JSON 파일 로드 실패: {e}")
        return []

STAGE_QUIZZES[1] = load_and_shuffle_quizzes(STAGE1_PATH, 1)
STAGE_QUIZZES[2] = load_and_shuffle_quizzes(STAGE2_PATH, 2)
STAGE_QUIZZES[3] = load_and_shuffle_quizzes(STAGE3_PATH, 3)

QUIZ_DATABASE = STAGE_QUIZZES[1] + STAGE_QUIZZES[2] + STAGE_QUIZZES[3]

try:
    with open(CARDS_PATH, "r", encoding="utf-8") as f:
        CARD_DATABASE = json.load(f)
except Exception as e:
    print(f"카드 JSON 파일 로드 실패: {e}")
    CARD_DATABASE = []

try:
    with open(ACHIEVEMENTS_PATH, "r", encoding="utf-8") as f:
        ACHIEVEMENTS_DATABASE = json.load(f)
except Exception as e:
    print(f"달성과제 JSON 파일 로드 실패: {e}")
    ACHIEVEMENTS_DATABASE = []

try:
    with open(REBIRTH_SHOP_PATH, "r", encoding="utf-8") as f:
        REBIRTH_SHOP_DATABASE = json.load(f)
except Exception as e:
    print(f"환생 상점 JSON 파일 로드 실패: {e}")
    REBIRTH_SHOP_DATABASE = []

# 2. 데이터 모델
class QuizBatchRequest(BaseModel):
    ids: List[str]

class VerifyRequest(BaseModel):
    quiz_id: str
    selected_index: int

class VerifyResponse(BaseModel):
    is_correct: bool
    correct_index: int
    explanation: str
    points: int

# 3. API 엔드포인트
@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "total_quizzes": len(QUIZ_DATABASE),
        "stage1_quizzes": len(STAGE_QUIZZES[1]),
        "stage2_quizzes": len(STAGE_QUIZZES[2]),
        "stage3_quizzes": len(STAGE_QUIZZES[3]),
        "total_cards": len(CARD_DATABASE),
        "total_achievements": len(ACHIEVEMENTS_DATABASE),
        "total_rebirth_shop_items": len(REBIRTH_SHOP_DATABASE)
    }

@app.get("/api/cards")
def get_cards():
    """도감 카드 데이터 목록 반환"""
    return CARD_DATABASE

@app.get("/api/achievements")
def get_achievements():
    """달성과제(업적) 마스터 목록 반환"""
    return ACHIEVEMENTS_DATABASE

@app.get("/api/rebirth-shop")
def get_rebirth_shop():
    """환생 상점 상품 목록 반환"""
    return REBIRTH_SHOP_DATABASE

@app.get("/api/quizzes/all")
def get_all_quizzes(stage: int = Query(default=1, ge=1, le=3)):
    """스테이지별 전체 퀴즈 데이터 목록 반환 (정답 정보 제외)"""
    target_quizzes = STAGE_QUIZZES.get(stage, [])
    if not target_quizzes:
        return []
    safe_quizzes = []
    for item in target_quizzes:
        safe_quizzes.append({
            "id": item["id"],
            "tier": item.get("tier", "초급"),
            "category": item.get("category", "기초"),
            "question": item["question"],
            "options": item["options"],
            "points": item.get("points", 100)
        })
    return safe_quizzes

@app.post("/api/quizzes/by-ids")
def get_quizzes_by_ids(req: QuizBatchRequest):
    """지정한 ID 목록 순서대로 퀴즈 반환"""
    if not QUIZ_DATABASE:
        return []
    quiz_map = {q["id"]: q for q in QUIZ_DATABASE}
    safe_quizzes = []
    for q_id in req.ids:
        if q_id in quiz_map:
            item = quiz_map[q_id]
            safe_quizzes.append({
                "id": item["id"],
                "tier": item.get("tier", "초급"),
                "category": item.get("category", "기초"),
                "question": item["question"],
                "options": item["options"],
                "points": item.get("points", 100)
            })
    return safe_quizzes

@app.get("/api/quizzes")
def get_random_quizzes(
    stage: int = Query(default=1, ge=1, le=3),
    count: int = Query(default=10, ge=1, le=100),
):
    """지정된 스테이지에서 count개를 무작위 선택하여 반환"""
    target_quizzes = STAGE_QUIZZES.get(stage, [])
    if not target_quizzes:
        return []
    
    selected = random.sample(target_quizzes, min(count, len(target_quizzes)))
    
    safe_quizzes = []
    for item in selected:
        safe_quizzes.append({
            "id": item["id"],
            "tier": item.get("tier", "초급"),
            "category": item.get("category", "기초"),
            "question": item["question"],
            "options": item["options"],
            "points": item.get("points", 100)
        })
    return safe_quizzes

@app.post("/api/quiz/verify", response_model=VerifyResponse)
def verify_answer(req: VerifyRequest):
    """정답 검증"""
    quiz = next((q for q in QUIZ_DATABASE if q["id"] == req.quiz_id), None)
    if not quiz:
        raise HTTPException(status_code=404, detail="해당 퀴즈를 찾을 수 없습니다.")

    if req.selected_index < -1 or req.selected_index >= len(quiz["options"]):
        raise HTTPException(status_code=422, detail="유효하지 않은 선택지입니다.")
    
    is_correct = (quiz["answer_index"] == req.selected_index)
    return VerifyResponse(
        is_correct=is_correct,
        correct_index=quiz["answer_index"],
        explanation=quiz.get("explanation", ""),
        points=quiz.get("points", 100) if is_correct else 0
    )
