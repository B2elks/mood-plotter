"""Answer judging — checks caller's transcribed answer against the question."""

import json
import os
import re
import urllib.request

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def judge_answer(question, transcript):
    """Judge if the transcript answers the question correctly.
    Returns {"correct": bool, "explanation": str}
    """
    if not transcript or not transcript.strip():
        return {"correct": False, "explanation": "Inget svar hördes."}

    q_type = question.get("type", "quiz")
    answer_text = transcript.strip()

    # Quiz: check against accept list
    if q_type == "quiz":
        accept = question.get("accept", [])
        answer_lower = answer_text.lower()
        for variant in accept:
            if variant.lower() in answer_lower:
                return {"correct": True, "explanation": f"Rätt! Svaret var {question['answer']}."}
        return _gpt_judge(question, answer_text)

    # Price/number: check range
    if q_type in ("price", "number"):
        accept_range = question.get("accept_range")
        if accept_range:
            num = _extract_number(answer_text)
            if num is not None and accept_range[0] <= num <= accept_range[1]:
                return {"correct": True, "explanation": f"Rätt! Svaret var {question['answer']}."}
            elif num is not None:
                return {"correct": False, "explanation": f"Tyvärr! Du sa {num}, rätt svar var {question['answer']}."}
        return _gpt_judge(question, answer_text)

    # Open: always GPT
    return _gpt_judge(question, answer_text)


def _extract_number(text):
    """Try to extract a number from text."""
    nums = re.findall(r'\d+', text.replace(" ", ""))
    if nums:
        return int(nums[0])
    return None


def _gpt_judge(question, answer_text):
    """Use GPT-4o-mini to judge an answer."""
    system_msg = (
        f"You are judging a game show answer. "
        f"Question: {question['question']}. "
        f"Correct answer: {question['answer']}. "
        f"The contestant said: \"{answer_text}\". "
        f"Is this correct or close enough? Reply with JSON: "
        f'{{"correct": true/false, "explanation": "short explanation in Swedish"}}'
    )

    data = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": answer_text},
        ],
        "max_tokens": 100,
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
    )

    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        content = result["choices"][0]["message"]["content"].strip()
        return json.loads(content)
    except Exception:
        return {"correct": False, "explanation": "Kunde inte bedöma svaret."}
