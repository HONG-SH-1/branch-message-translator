"""번역 품질 검증용 프로브 (2차 검증: 베트남어/스페인어 + 역번역).

타깃 언어(베트남어/스페인어)는 검토자가 직접 읽기 어려우므로,
KO → 타깃 → KO 역번역으로 의미 보존 여부를 한국어로 확인한다.
(제출용 기능이 아니라 검증 도구)

실행: GOOGLE_APPLICATION_CREDENTIALS 설정 후
  .\.venv\Scripts\python.exe 품질테스트.py
"""

import json
import os

from google import genai
from google.genai import types

cred = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
PROJECT = json.load(open(cred, encoding="utf-8"))["project_id"]
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)

TARGETS = {"vi": "베트남어", "es": "스페인어"}

SAMPLES = [
    ("먹었어?", "주어 생략"),
    ("생각해보겠습니다.", "정중한 거절(반어 가능성)"),
    ("아 죽겠다, 일이 너무 많아.", "관용구/과장"),
    ("이번 발주 건 납기 좀 앞당겨 주실 수 있을까요?", "비즈니스 존대"),
]


def gen(prompt: str) -> str:
    r = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2),
    )
    return r.text.strip()


def forward(text: str, lang_name: str) -> str:
    return gen(
        f"당신은 제조업 지사 간 업무 메시지를 번역하는 전문 번역가입니다.\n"
        f"아래 한국어를 {lang_name}로 정중한 비즈니스 톤으로 번역하세요. 번역문만 출력.\n\n[원문]\n{text}"
    )


def back(text: str, lang_name: str) -> str:
    return gen(
        f"다음 {lang_name} 문장을 한국어로 직역하세요. 번역문만 출력.\n\n{text}"
    )


lines = []
for text, note in SAMPLES:
    lines.append(f"\n===== [{note}] 원문: {text} =====")
    for code, lang_name in TARGETS.items():
        translated = forward(text, lang_name)
        round_trip = back(translated, lang_name)
        lines.append(f"  [{lang_name}] {translated}")
        lines.append(f"    -> 역번역(KO): {round_trip}")

output = "\n".join(lines)
with open("result.txt", "w", encoding="utf-8") as f:
    f.write(output)
print("saved to result.txt")
