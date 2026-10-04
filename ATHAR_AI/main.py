import sys

import database
from agent import AtharAgent


def show_banner():
    print("""
╔══════════════════════════════════════════════╗
║              ATHAR AI AGENT                  ║
║                  v1.1.0                      ║
║                                              ║
║       Intelligent Autonomous Agent           ║
╚══════════════════════════════════════════════╝
""")


def show_help():
    print("""
الأوامر:

  task <المهمة>
      تنفيذ مهمة جديدة

  tasks
      عرض آخر المهام

  memory
      عرض الذاكرة

  init
      تهيئة قاعدة البيانات

  help
      عرض المساعدة

  exit
      الخروج

ملاحظة:
داخل ATHAR اكتب المهمة فقط، بدون ATHAR > وبدون python main.py.
""")


def run():

    database.init_db()

    show_banner()

    if len(sys.argv) > 1:

        command = sys.argv[1]

        if command == "init":
            database.init_db()
            print("تم إنشاء قاعدة البيانات.")
            return

        if command == "tasks":
            tasks = database.get_tasks()

            if not tasks:
                print("لا توجد مهام.")
                return

            print("\nآخر المهام:\n")

            for item in tasks:
                print(
                    f"[{item['id']}] "
                    f"{item['status']} - "
                    f"{item['task']}"
                )

            return

        if command == "memory":
            memories = database.get_memories()

            if not memories:
                print("لا توجد ذاكرة.")
                return

            print("\nذاكرة ATHAR:\n")

            for item in memories:
                print(
                    f"- {item['key']}: "
                    f"{item['value']}"
                )

            return

        if command == "help":
            show_help()
            return

        if command == "task":

            if len(sys.argv) < 3:
                print(
                    "خطأ: اكتب المهمة بعد task."
                )
                return

            task = " ".join(sys.argv[2:]).strip()

            agent = AtharAgent()
            agent.execute(task)

            return

        print(
            f"أمر غير معروف: {command}"
        )

        show_help()
        return

    interactive_mode()


def interactive_mode():

    agent = AtharAgent()

    print(
        "اكتب مهمتك مباشرة.\n"
        "مثال: أنشئ خطة لتطوير مشروع ذكاء اصطناعي\n"
    )

    while True:

        try:
            task = input(
                "ATHAR > "
            ).strip()

        except KeyboardInterrupt:
            print("\n\nتم إيقاف ATHAR AI.")
            break

        if not task:
            continue

        if task.lower() in [
            "exit",
            "quit",
            "خروج"
        ]:
            print("\nتم إيقاف ATHAR AI.")
            break

        if task.lower() in [
            "help",
            "مساعدة"
        ]:
            show_help()
            continue

        # منع إدخال أوامر Terminal بالخطأ
        if task.startswith("python main.py"):
            print(
                "\nأنت داخل ATHAR بالفعل."
                "\nاكتب المهمة مباشرة فقط."
                "\nمثال:"
                "\n  أنشئ خطة لتطوير مشروع ذكاء اصطناعي\n"
            )
            continue

        # إزالة prompt إذا نسخه المستخدم بالخطأ
        if task.startswith("ATHAR >"):
            task = task.replace(
                "ATHAR >",
                "",
                1
            ).strip()

        if not task:
            continue

        try:
            agent.execute(task)

        except Exception as exc:
            print(
                f"\nفشل التنفيذ: {exc}\n"
            )


if __name__ == "__main__":
    run()
