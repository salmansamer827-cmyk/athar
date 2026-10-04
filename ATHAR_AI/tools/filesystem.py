import os


def list_files(path="."):
    results = []

    for root, dirs, files in os.walk(path):
        for filename in files:
            results.append(
                os.path.join(root, filename)
            )

    return results


def read_file(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def write_file(path, content):
    parent = os.path.dirname(path)

    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)

    return f"تم إنشاء الملف: {path}"
