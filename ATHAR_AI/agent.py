import database
import planner
import memory

from config import MAX_STEPS


class AtharAgent:

    def __init__(self):
        database.init_db()

    def execute(self, task):

        print("\n" + "=" * 60)
        print("ATHAR AI")
        print("=" * 60)

        print(f"\nالمهمة:")
        print(task)

        task_id = database.create_task(task)

        try:
            memory_context = memory.build_memory_context()

            print("\n[1] تحليل المهمة...")

            plan = planner.create_plan(
                task,
                memory_context
            )

            goal = plan.get(
                "goal",
                task
            )

            steps = plan.get(
                "steps",
                []
            )

            steps = steps[:MAX_STEPS]

            print(f"\nالهدف: {goal}")

            if not steps:
                raise RuntimeError(
                    "لم يتم إنشاء خطة تنفيذ."
                )

            print(
                f"\n[2] تم إنشاء الخطة: "
                f"{len(steps)} خطوات"
            )

            results = []

            for index, step in enumerate(
                steps,
                start=1
            ):

                description = step[
                    "description"
                ]

                print(
                    f"\n[STEP {index}] "
                    f"{description}"
                )

                step_id = database.add_step(
                    task_id,
                    index,
                    description
                )

                database.update_step(
                    step_id,
                    "completed",
                    "تم تسجيل الخطوة ضمن خطة التنفيذ."
                )

                results.append({
                    "step": index,
                    "description": description,
                    "status": "completed"
                })

            final_result = {
                "goal": goal,
                "steps": results
            }

            database.complete_task(
                task_id,
                str(final_result)
            )

            memory.remember(
                "last_task",
                task
            )

            print("\n[3] اكتملت دورة الوكيل.")

            return final_result

        except Exception as exc:

            database.fail_task(
                task_id,
                str(exc)
            )

            print(
                f"\n[ERROR] {exc}"
            )

            raise
