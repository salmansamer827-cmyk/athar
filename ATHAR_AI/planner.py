import json
import requests

from config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    MAX_STEPS
)


SYSTEM_PROMPT = f"""
أنت Planner داخل ATHAR AI.

مهمتك تحليل طلب المستخدم وتحويله إلى خطة تنفيذ عملية.

يجب أن تعيد JSON فقط بهذا الشكل:

{{
  "goal": "الهدف النهائي",
  "steps": [
    {{
      "description": "خطوة عملية وواضحة"
    }}
  ]
}}

القواعد:

1. حلل المهمة قبل إنشاء الخطة.
2. قسم المهمة إلى خطوات منطقية.
3. اجعل كل خطوة قابلة للتنفيذ.
4. لا تتجاوز {MAX_STEPS} خطوات.
5. لا تنفذ المهمة.
6. لا تضف أي نص خارج JSON.
"""


def create_plan(task, memory_context=""):

    if not OPENAI_API_KEY:
        print(
            "[PLANNER] وضع محلي: "
            "OPENAI_API_KEY غير موجود."
        )

        return local_plan(task)

    print(
        f"[PLANNER] AI Model: {OPENAI_MODEL}"
    )

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": (
                    f"الذاكرة السابقة:\n"
                    f"{memory_context}\n\n"
                    f"المهمة الحالية:\n"
                    f"{task}"
                )
            }
        ],
        "temperature": 0.2
    }

    response = requests.post(
        f"{OPENAI_BASE_URL}/chat/completions",
        headers={
            "Authorization":
                f"Bearer {OPENAI_API_KEY}",
            "Content-Type":
                "application/json"
        },
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    content = data[
        "choices"
    ][0][
        "message"
    ][
        "content"
    ]

    content = content.strip()

    # إزالة markdown JSON إذا أعاده النموذج
    if content.startswith("```"):
        content = content.replace(
            "```json",
            "",
            1
        ).replace(
            "```",
            "",
            1
        ).strip()

    plan = json.loads(content)

    if not isinstance(plan, dict):
        raise ValueError(
            "استجابة Planner غير صحيحة."
        )

    return plan


def local_plan(task):

    return {
        "goal": task,
        "steps": [
            {
                "description":
                    "تحليل المهمة وتحديد المتطلبات."
            },
            {
                "description":
                    "تحديد الموارد والأدوات المطلوبة."
            },
            {
                "description":
                    "تنفيذ الخطوات المطلوبة بالترتيب."
            },
            {
                "description":
                    "التحقق من النتيجة وإعداد التقرير النهائي."
            }
        ]
    }
