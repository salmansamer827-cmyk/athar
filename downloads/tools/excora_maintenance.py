#!/usr/bin/env python3

from pathlib import Path
import os
import shutil
import sys
import time


# ============================================================
# EXCORA MAINTENANCE V1
# Lightweight Termux Project Maintenance Tool
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

SAFE_PATTERNS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

SAFE_SUFFIXES = {
    ".pyc",
    ".pyo",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
}


def human_size(size):
    units = ["B", "KB", "MB", "GB"]
    value = float(size)

    for unit in units:
        if value < 1024:
            return f"{value:.2f} {unit}"
        value /= 1024

    return f"{value:.2f} TB"


def directory_size(path):
    total = 0

    try:
        for root, dirs, files in os.walk(path):
            dirs[:] = [
                d for d in dirs
                if d not in SKIP_DIRS
            ]

            for name in files:
                try:
                    total += (Path(root) / name).stat().st_size
                except OSError:
                    pass

    except OSError:
        pass

    return total


def print_header():
    print()
    print("=" * 60)
    print("              EXCORA MAINTENANCE V1")
    print("=" * 60)
    print(f"Project: {ROOT}")
    print("=" * 60)


def project_info():
    print()
    print("[ PROJECT INFORMATION ]")

    size = directory_size(ROOT)

    print(f"Project size : {human_size(size)}")

    try:
        files = 0
        folders = 0

        for root, dirs, filenames in os.walk(ROOT):
            dirs[:] = [
                d for d in dirs
                if d not in SKIP_DIRS
            ]

            folders += len(dirs)
            files += len(filenames)

        print(f"Files        : {files}")
        print(f"Directories  : {folders}")

    except OSError:
        pass


def find_junk():
    found = []

    for root, dirs, files in os.walk(ROOT):

        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS
        ]

        for directory in dirs:
            if directory in SAFE_PATTERNS:
                found.append(Path(root) / directory)

        for filename in files:
            path = Path(root) / filename

            if path.suffix in SAFE_SUFFIXES:
                found.append(path)

    return found


def junk_size(items):
    total = 0

    for item in items:

        try:
            if item.is_dir():
                total += directory_size(item)
            else:
                total += item.stat().st_size

        except OSError:
            pass

    return total


def scan():
    print()
    print("[ SCAN ]")

    items = find_junk()

    if not items:
        print("No safe temporary files found.")
        return

    size = junk_size(items)

    print(f"Temporary items : {len(items)}")
    print(f"Recoverable     : {human_size(size)}")

    print()

    for item in items[:50]:
        print(f"  {item}")

    if len(items) > 50:
        print(f"\n... and {len(items) - 50} more.")


def clean():

    print()
    print("[ SAFE CLEANUP ]")

    items = find_junk()

    if not items:
        print("Nothing to clean.")
        return

    before = junk_size(items)

    print(f"Found : {len(items)} items")
    print(f"Size  : {human_size(before)}")

    answer = input("\nDelete these safe temporary files? [y/N]: ")

    if answer.lower() != "y":
        print("Cancelled.")
        return

    deleted = 0
    failed = 0

    for item in items:

        try:

            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

            deleted += 1

        except OSError:
            failed += 1

    after = directory_size(ROOT)

    print()
    print("Cleanup completed.")
    print(f"Deleted : {deleted}")
    print(f"Failed  : {failed}")
    print(f"Project : {human_size(after)}")


def system_cache():

    print()
    print("[ TERMUX CACHE ]")

    paths = [
        Path.home() / ".cache",
        Path.home() / ".cache" / "pip",
        Path.home() / ".npm",
    ]

    for path in paths:

        if path.exists():

            try:
                size = directory_size(path)
                print(f"{path} -> {human_size(size)}")

            except OSError:
                print(f"{path} -> inaccessible")

        else:
            print(f"{path} -> not found")


def menu():

    while True:

        print()
        print("-" * 60)
        print("1. Project information")
        print("2. Scan temporary files")
        print("3. Safe cleanup")
        print("4. Check Termux cache")
        print("5. Full safe scan")
        print("0. Exit")
        print("-" * 60)

        choice = input("EXCORA > ").strip()

        if choice == "1":
            project_info()

        elif choice == "2":
            scan()

        elif choice == "3":
            clean()

        elif choice == "4":
            system_cache()

        elif choice == "5":
            project_info()
            scan()
            system_cache()

        elif choice == "0":
            print("\nEXCORA Maintenance closed.")
            break

        else:
            print("Invalid option.")


def main():

    if not ROOT.exists():
        print("EXCORA project directory not found.")
        sys.exit(1)

    print_header()
    menu()


if __name__ == "__main__":
    main()
