import database


def remember(key, value):
    database.save_memory(key, value)


def recall(limit=20):
    return database.get_memories(limit)


def build_memory_context(limit=10):

    memories = recall(limit)

    if not memories:
        return "لا توجد ذاكرة سابقة."

    lines = []

    for item in memories:
        lines.append(
            f"- {item['key']}: {item['value']}"
        )

    return "\n".join(lines)
