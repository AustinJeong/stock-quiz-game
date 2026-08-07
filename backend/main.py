from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Stock Quiz Game API")

# 1. CORS 설정: Vercel 프론트엔드에서 백엔드 API로 들어오는 요청 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실운영 시 특정 Vercel 도메인(예: ["https://my-stock.vercel.app"])으로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 데이터 모델 정의
class QuizItem(BaseModel):
    id: str
    tier: str
    category: str
    question: str
    options: List[str]
    points: int

class VerifyRequest(BaseModel):
    quiz_id: str
    selected_index: int

class VerifyResponse(BaseModel):
    is_correct: bool
    correct_index: int
    explanation: str
    points: int

# 3. 주식 퀴즈 데이터베이스 (예시 데이터)
QUIZ_DATABASE = [
    {
        "id": "quiz_beg_001",
        "tier": "초급",
        "category": "기초용어",
        "question": "주가를 1주당 순이익(EPS)으로 나눈 지표로, 주가가 1주당 순이익의 몇 배에 거래되는지 나타내는 것은?",
        "options": ["PBR (주가순자산비율)", "PER (주가수익비율)", "ROE (자기자본이익률)", "EV/EBITDA"],
        "answer_index": 1,
        "explanation": "PER(Price Earnings Ratio, 주가수익비율)은 현재 주가를 1주당 순이익(EPS)으로 나눈 값입니다.",
        "points": 100
    },
    {
        "id": "quiz_beg_002",
        "tier": "초급",
        "category": "시장제도",
        "question": "한국 주식 시장에서 매수 주문 체결 후 실제 주식 입고 및 대금 결제가 완료되는 시점은?",
        "options": ["매수 즉시 (T+0)", "다음 영업일 (T+1)", "영업일 기준 2일 후 (T+2)", "영업일 기준 3일 후 (T+3)"],
        "answer_index": 2,
        "explanation": "한국 주식 시장은 T+2일 주식 결제 제도를 채택하고 있습니다.",
        "points": 100
    },
    {
        "id": "quiz_mid_001",
        "tier": "중급",
        "category": "기술적분석",
        "question": "단기 이동평균선이 장기 이동평균선을 아래에서 위로 뚫고 올라가는 상승 추세 전환 신호는?",
        "options": ["데드크로스", "골든크로스", "볼린저밴드 상단 돌파", "눌림목"],
        "answer_index": 1,
        "explanation": "골든크로스는 단기 이평선이 장기 이평선을 상향 돌파하는 강한 매수 신호로 해석됩니다.",
        "points": 200
    },
    {
        "id": "quiz_adv_001",
        "tier": "상급",
        "category": "공시/특수상황",
        "question": "기준주가 10,000원인 기업이 발행가액 5,000원에 주당 0.2주(20%) 유상증자를 단행할 때 권리락 기준가는?",
        "options": ["8,500원", "9,000원", "9,167원", "9,500원"],
        "answer_index": 2,
        "explanation": "권리락 기준가 = (기존주가 + 발행가액 × 증자비율) / (1 + 증자비율) = (10,000 + 1,000) / 1.2 = 9,166.6...원입니다.",
        "points": 300
    }
]

# 4. API 엔드포인트

@app.get("/")
@app.get("/health")
def health_check():
    """서버 헬스체크 및 UptimeRobot 슬립 방지용"""
    return {"status": "ok", "message": "Stock Quiz API Server is Live!"}

@app.get("/api/quizzes", response_model=List[QuizItem])
def get_quizzes():
    """프론트엔드용 퀴즈 목록 반환 (정답 정보 제외)"""
    safe_quizzes = []
    for item in QUIZ_DATABASE:
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
    """유저 답안 검증 엔드포인트"""
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
