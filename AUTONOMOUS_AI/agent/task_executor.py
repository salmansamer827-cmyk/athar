from core.console import log


class TaskExecutor:

    def execute(self, plan):
        results = []

        for step in plan:
            log(
                f"Step {step['step']}: "
                f"{step['description']}"
            )

            results.append({
                "step": step["step"],
                "status": "completed",
                "action": step["action"]
            })

        return results
