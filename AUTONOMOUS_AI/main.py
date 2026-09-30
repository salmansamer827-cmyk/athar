from agent.orchestrator import MasterAgent


def main():

    agent = MasterAgent()

    print()
    print("AUTONOMOUS AI")
    print("اكتب المهمة التي تريد من الوكيل تنفيذها.")
    print("اكتب exit للخروج.")
    print()

    while True:

        task = input("You > ").strip()

        if task.lower() == "exit":
            print("Master Agent stopped.")
            break

        if not task:
            continue

        agent.run(task)


if __name__ == "__main__":
    main()
