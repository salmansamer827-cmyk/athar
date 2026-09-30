from core.console import log


class Planner:

    def create_plan(self, task: str):
        log(f"تحليل المهمة: {task}")

        plan = [
            {
                "step": 1,
                "action": "understand",
                "description": "فهم طلب المستخدم"
            },
            {
                "step": 2,
                "action": "plan",
                "description": "تحديد خطوات التنفيذ"
            },
            {
                "step": 3,
                "action": "execute",
                "description": "تنفيذ المهمة"
            },
            {
                "step": 4,
                "action": "verify",
                "description": "التحقق من النتيجة"
            }
        ]

        return plan
