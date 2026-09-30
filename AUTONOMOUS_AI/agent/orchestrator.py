from core.console import banner, log
from agent.planner import Planner
from agent.task_executor import TaskExecutor


class MasterAgent:

    def __init__(self):
        self.planner = Planner()
        self.executor = TaskExecutor()

    def run(self, task: str):

        banner()

        log("Master Agent started")

        log(f"New task received: {task}")

        plan = self.planner.create_plan(task)

        log(f"Plan created: {len(plan)} steps")

        results = self.executor.execute(plan)

        completed = sum(
            1 for result in results
            if result["status"] == "completed"
        )

        log(
            f"Task completed: "
            f"{completed}/{len(results)} steps"
        )

        return {
            "task": task,
            "plan": plan,
            "results": results,
            "status": "completed"
        }
