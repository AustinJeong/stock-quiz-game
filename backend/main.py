from fastapi import FastAPI, HTTPException
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
JSON_PATH = os.path.join(BASE_DIR, "stage1_quizzes.json")

try:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        QUIZ_DATABASE = json.load(f)
    
    # ★ 핵심: 서버 실행 시 보기(options)를 무작위로 섞고 정답 인덱스(answer_index)를 자동 재설정
    for quiz in QUIZ_DATABASE:
        correct_text = quiz["options"][quiz["answer_index"]]  # 원래 정답 텍스트 보관
        random.shuffle(quiz["options"])                      # 보기 순서 무작위 셔플
        quiz["answer_index"] = quiz["options"].index(correct_text)  # 새로 섞인 정답 위치 반영

except Exception as e:
    print(f"JSON 파일 로드 실패: {e}")
    QUIZ_DATABASE = []

# 2. 데이터 모델
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
    return {"status": "ok", "total_quizzes": len(QUIZ_DATABASE)}

@app.get("/api/quizzes")
def get_random_quizzes(count: int = 10):
    """100문제 중 무작위로 count개(기본 5개)를 무작위 선택하여 반환"""
    if not QUIZ_DATABASE:
        return []
    
    selected = random.sample(QUIZ_DATABASE, min(count, len(QUIZ_DATABASE)))
    
    safe_quizzes = []
    for item in selected:
        safe_quizzes.append({
            "id": item["id"],
            "tier": item["tier"],
            "category": item["category"],
            "question": item["question"],
            "options": item["options"],
            "points": item["points"]
        })
    return safe_quizzes

@app.post("/api/quiz/verify", response_model=VerifyResponse)
def verify_answer(req: VerifyRequest):
    """정답 검증"""
    quiz = next((q for q in QUIZ_DATABASE if q["id"] == req.quiz_id), None)
    if not quiz:
        raise HTTPException(status_code=404, detail="해당 퀴즈를 찾을 수 없습니다.")
    
    is_correct = (quiz["answer_index"] == req.selected_index)
    return VerifyResponse(
        is_correct=is_correct,
        correct_index=quiz["answer_index"],
        explanation=quiz["explanation"],
        points=quiz["points"] if is_correct else 0
    )
