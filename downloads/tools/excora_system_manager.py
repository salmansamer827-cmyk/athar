#!/usr/bin/env python3

from pathlib import Path
import os
import shutil
import subprocess
import sys
import hashlib
import time


# ============================================================
# EXCORA SYSTEM MANAGER
# Integrated Termux / Project Cleanup Manager
# ============================================================

HOME = Path.home()
ROOT = Path(__file__).resolve().parent.parent

VERSION = "2.0"


# ============================================================
# PROTECTED LOCATIONS
# ============================================================

PROTECTED_NAMES = {
    ".env",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "Cargo.toml",
    "Cargo.lock",
}


PROTECTED_PROJECTS = {
    "EXCORA",
    "EXCORA_V10",
    "capital-wise",
    "valora",
}


TEMP_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
}


TEMP_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".tmp",
    ".temp",
    ".log",
}


# ============================================================
# BASIC UTILITIES
# ============================================================

def human(size):

    units = ["B", "KB", "MB", "GB", "TB"]

    value = float(size)

    for unit in units:

        if value < 1024:
            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{value:.2f} PB"


def path_size(path):

    total = 0

    try:

        if path.is_file():
            return path.stat().st_size

        for root, dirs, files in os.walk(path):

            for name in files:

                try:
                    total += (
                        Path(root) / name
                    ).stat().st_size

                except OSError:
                    pass

    except OSError:
        pass

    return total


def run(command):

    try:

        return subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    except Exception:

        return None


def confirm(message):

    answer = input(
        f"\n{message} [y/N]: "
    ).strip().lower()

    return answer == "y"


def protected(path):

    parts = set(path.parts)

    if parts & PROTECTED_NAMES:
        return True

    return False


# ============================================================
# HEADER
# ============================================================

def header(title):

    print()
    print("=" * 64)
    print(f"EXCORA SYSTEM MANAGER {VERSION}")
    print(title)
    print("=" * 64)


# ============================================================
# STORAGE
# ============================================================

def storage():

    header("STORAGE ANALYZER")

    result = run(["df", "-h"])

    if result and result.stdout:

        print(result.stdout)

    else:

        print("Storage information unavailable.")


# ============================================================
# DIRECTORY ANALYZER
# ============================================================

def directory_report(base):

    results = []

    if not base.exists():
        return results

    try:

        for item in base.iterdir():

            if item.name in {
                ".git",
                ".cache",
            }:
                continue

            try:
                results.append(
                    (
                        path_size(item),
                        item
                    )
                )

            except OSError:
                pass

    except OSError:
        pass

    results.sort(reverse=True)

    return results


def home_report():

    header("HOME STORAGE")

    results = directory_report(HOME)

    for value, path in results[:30]:

        print(
            f"{human(value):>12}  {path.name}"
        )


# ============================================================
# EXCORA REPORT
# ============================================================

def excora_report():

    header("EXCORA PROJECT")

    for project in PROTECTED_PROJECTS:

        path = HOME / project

        if path.exists():

            print(
                f"{project:<20} "
                f"{human(path_size(path))}"
            )


# ============================================================
# TEMPORARY FILE SCANNER
# ============================================================

def temporary_items(base):

    found = []

    if not base.exists():
        return found

    for root, dirs, files in os.walk(base):

        dirs[:] = [
            d for d in dirs
            if d not in {
                ".git",
                ".venv",
                "venv",
                "node_modules"
            }
        ]

        for directory in dirs:

            if directory in TEMP_DIR_NAMES:

                path = Path(root) / directory

                if not protected(path):
                    found.append(path)

        for filename in files:

            path = Path(root) / filename

            if (
                path.suffix.lower()
                in TEMP_EXTENSIONS
            ):

                if not protected(path):
                    found.append(path)

    return found


def temp_scan():

    header("TEMPORARY FILES")

    items = temporary_items(HOME)

    total = sum(
        path_size(item)
        for item in items
    )

    print(f"Items       : {len(items)}")
    print(f"Recoverable : {human(total)}")

    for item in items[:50]:

        print(
            f"{human(path_size(item)):>12} "
            f"{item}"
        )


def temp_clean():

    header("TEMPORARY CLEANUP")

    items = temporary_items(HOME)

    total = sum(
        path_size(item)
        for item in items
    )

    print(
        f"Found: {len(items)}"
    )

    print(
        f"Recoverable: {human(total)}"
    )

    if not items:
        return

    if not confirm(
        "Delete ONLY temporary files?"
    ):
        print("Cancelled.")
        return

    before = path_size(HOME)

    deleted = 0

    for item in items:

        try:

            if protected(item):
                continue

            if item.is_dir():

                shutil.rmtree(item)

            else:

                item.unlink()

            deleted += 1

        except OSError:
            pass

    after = path_size(HOME)

    print()
    print(f"Deleted : {deleted}")
    print(
        f"Recovered: {human(max(0, before-after))}"
    )


# ============================================================
# PIP
# ============================================================

def pip_manager():

    header("PIP CACHE")

    result = run([
        sys.executable,
        "-m",
        "pip",
        "cache",
        "info"
    ])

    if result:

        print(
            result.stdout
            or result.stderr
        )

    print()

    if confirm(
        "Clean PIP cache?"
    ):

        result = run([
            sys.executable,
            "-m",
            "pip",
            "cache",
            "purge"
        ])

        if result:

            print(
                result.stdout
                or result.stderr
            )


# ============================================================
# VIRTUAL ENVIRONMENT SCANNER
# ============================================================

def find_venvs():

    results = []

    for item in HOME.iterdir():

        if not item.is_dir():
            continue

        python = (
            item / "bin" / "python"
        )

        if python.exists():

            results.append(item)

    return results


def venv_manager():

    header("PYTHON VIRTUAL ENVIRONMENTS")

    venvs = find_venvs()

    if not venvs:

        print("No virtual environments found.")
        return

    for index, env in enumerate(
        venvs,
        1
    ):

        print(
            f"{index}. "
            f"{env.name:<35} "
            f"{human(path_size(env))}"
        )

    print()
    print(
        "Protected projects are never "
        "deleted automatically."
    )

    choice = input(
        "\nEnter number to inspect, "
        "or 0 to return: "
    ).strip()

    if choice == "0":
        return

    try:

        index = int(choice) - 1
        env = venvs[index]

    except Exception:

        print("Invalid selection.")
        return

    print()
    print(f"Selected: {env}")
    print(f"Size    : {human(path_size(env))}")

    if env.name in {
        "venv",
        ".venv"
    }:

        print(
            "This environment has a generic "
            "name and will NOT be deleted "
            "automatically."
        )

        return

    if confirm(
        f"DELETE virtual environment {env.name}?"
    ):

        shutil.rmtree(env)

        print("Virtual environment deleted.")


# ============================================================
# CARGO
# ============================================================

def cargo_manager():

    header("CARGO STORAGE")

    cargo = HOME / ".cargo"

    if not cargo.exists():

        print("Cargo directory not found.")
        return

    registry = cargo / "registry"
    cache = registry / "cache"
    source = registry / "src"

    print(
        f"Cargo total : {human(path_size(cargo))}"
    )

    print(
        f"Registry    : {human(path_size(registry))}"
    )

    print(
        f"Cache       : {human(path_size(cache))}"
    )

    print(
        f"Source      : {human(path_size(source))}"
    )

    print()

    print(
        "Cargo registry contains downloaded "
        "Rust crates."
    )

    print(
        "Removing it does NOT remove Cargo itself."
    )

    if confirm(
        "Remove Cargo registry cache/source?"
    ):

        if registry.exists():

            shutil.rmtree(registry)

            print(
                "Cargo registry removed."
            )

            print(
                "It will be downloaded again "
                "when required."
            )


# ============================================================
# NPM
# ============================================================

def npm_manager():

    header("NODE / NPM")

    npm = HOME / ".npm"

    if npm.exists():

        print(
            f"NPM cache: "
            f"{human(path_size(npm))}"
        )

    else:

        print("NPM cache not found.")

    result = run([
        "npm",
        "--version"
    ])

    if result:

        print(
            f"NPM version: "
            f"{result.stdout.strip()}"
        )

    if npm.exists():

        if confirm(
            "Clean NPM cache?"
        ):

            result = run([
                "npm",
                "cache",
                "clean",
                "--force"
            ])

            if result:

                print(
                    result.stdout
                    or result.stderr
                )


# ============================================================
# LARGE FILES
# ============================================================

def large_files():

    header("LARGE FILE SCANNER")

    results = []

    for root, dirs, files in os.walk(HOME):

        dirs[:] = [
            d for d in dirs
            if d not in {
                ".git",
                ".cargo",
                ".cache",
                "node_modules"
            }
        ]

        for name in files:

            path = Path(root) / name

            try:

                value = path.stat().st_size

                results.append(
                    (value, path)
                )

            except OSError:
                pass

    results.sort(reverse=True)

    for value, path in results[:40]:

        print(
            f"{human(value):>12} "
            f"{path}"
        )


# ============================================================
# DUPLICATE SCANNER
# ============================================================

def file_hash(path):

    try:

        digest = hashlib.sha256()

        with open(
            path,
            "rb"
        ) as file:

            while True:

                block = file.read(
                    1024 * 1024
                )

                if not block:
                    break

                digest.update(block)

        return digest.hexdigest()

    except Exception:

        return None


def duplicate_scan():

    header("DUPLICATE FILE SCANNER")

    groups = {}

    for root, dirs, files in os.walk(HOME):

        dirs[:] = [
            d for d in dirs
            if d not in {
                ".git",
                ".cargo",
                ".cache",
                "node_modules",
            }
        ]

        for name in files:

            path = Path(root) / name

            try:

                value = path.stat().st_size

            except OSError:

                continue

            if value < 1024 * 1024:
                continue

            groups.setdefault(
                value,
                []
            ).append(path)

    duplicates = []

    for value, paths in groups.items():

        if len(paths) < 2:
            continue

        hashes = {}

        for path in paths:

            digest = file_hash(path)

            if digest:

                hashes.setdefault(
                    digest,
                    []
                ).append(path)

        for digest, same in hashes.items():

            if len(same) > 1:

                duplicates.append(
                    (value, same)
                )

    if not duplicates:

        print(
            "No large duplicates found."
        )

        return

    for value, paths in duplicates:

        print()
        print(
            f"Duplicate size: {human(value)}"
        )

        for path in paths:

            print(
                f"  {path}"
            )


# ============================================================
# ANDROID APPLICATION MANAGER
# ============================================================

def android_apps():

    header("ANDROID APPLICATIONS")

    result = run([
        "pm",
        "list",
        "packages",
        "-3"
    ])

    if not result:

        print(
            "Android package manager unavailable."
        )

        return

    if result.returncode != 0:

        print(
            result.stderr.strip()
        )

        return

    packages = []

    for line in result.stdout.splitlines():

        if line.startswith(
            "package:"
        ):

            packages.append(
                line.split(
                    ":",
                    1
                )[1]
            )

    print(
        f"User applications: "
        f"{len(packages)}"
    )

    for index, package in enumerate(
        packages,
        1
    ):

        print(
            f"{index:3}. {package}"
        )

    print()
    print(
        "Android app removal requires "
        "explicit confirmation."
    )

    choice = input(
        "\nEnter package name to uninstall "
        "or 0 to return: "
    ).strip()

    if choice == "0":
        return

    if choice not in packages:

        print(
            "Package is not in the user-app list."
        )

        return

    if confirm(
        f"UNINSTALL {choice}?"
    ):

        result = run([
            "pm",
            "uninstall",
            choice
        ])

        if result:

            print(
                result.stdout
                or result.stderr
            )


# ============================================================
# SYSTEM INFORMATION
# ============================================================

def system_info():

    header("SYSTEM INFORMATION")

    commands = [
        ["uname", "-a"],
        ["python", "--version"],
        ["pip", "--version"],
        ["node", "--version"],
        ["npm", "--version"],
        ["cargo", "--version"],
    ]

    for command in commands:

        result = run(command)

        if not result:
            continue

        output = (
            result.stdout.strip()
            or result.stderr.strip()
        )

        print(
            f"{' '.join(command):25} "
            f"{output}"
        )


# ============================================================
# FULL REPORT
# ============================================================

def full_report():

    storage()
    home_report()
    excora_report()
    temp_scan()
    system_info()


# ============================================================
# SAFE CLEANUP
# ============================================================

def safe_cleanup():

    header("SAFE CLEANUP")

    print(
        "The following operations are considered "
        "low-risk:"
    )

    print()
    print("[1] Temporary files")
    print("[2] PIP cache")
    print("[3] NPM cache")
    print("[4] All safe cleanup")
    print("[0] Return")

    choice = input(
        "\nEXCORA > "
    ).strip()

    if choice == "1":

        temp_clean()

    elif choice == "2":

        pip_manager()

    elif choice == "3":

        npm_manager()

    elif choice == "4":

        temp_clean()
        pip_manager()
        npm_manager()


# ============================================================
# MAIN MENU
# ============================================================

def menu():

    while True:

        print()
        print(
            "╔══════════════════════════════════════════════╗"
        )

        print(
            "║       EXCORA SYSTEM MANAGER V2              ║"
        )

        print(
            "╠══════════════════════════════════════════════╣"
        )

        print(
            "║  1  Storage Analyzer                         ║"
        )

        print(
            "║  2  Home Storage Report                      ║"
        )

        print(
            "║  3  EXCORA Project Report                    ║"
        )

        print(
            "║  4  Temporary Cleanup                        ║"
        )

        print(
            "║  5  PIP Manager                              ║"
        )

        print(
            "║  6  Virtual Environment Manager              ║"
        )

        print(
            "║  7  Cargo Manager                            ║"
        )

        print(
            "║  8  NPM Manager                              ║"
        )

        print(
            "║  9  Large Files Scanner                      ║"
        )

        print(
            "║ 10  Duplicate Scanner                        ║"
        )

        print(
            "║ 11  Android App Manager                      ║"
        )

        print(
            "║ 12  System Information                       ║"
        )

        print(
            "║ 13  Full Diagnostic                           ║"
        )

        print(
            "║ 14  Safe Cleanup                              ║"
        )

        print(
            "║  0  Exit                                      ║"
        )

        print(
            "╚══════════════════════════════════════════════╝"
        )

        choice = input(
            "\nEXCORA > "
        ).strip()

        if choice == "1":
            storage()

        elif choice == "2":
            home_report()

        elif choice == "3":
            excora_report()

        elif choice == "4":
            temp_clean()

        elif choice == "5":
            pip_manager()

        elif choice == "6":
            venv_manager()

        elif choice == "7":
            cargo_manager()

        elif choice == "8":
            npm_manager()

        elif choice == "9":
            large_files()

        elif choice == "10":
            duplicate_scan()

        elif choice == "11":
            android_apps()

        elif choice == "12":
            system_info()

        elif choice == "13":
            full_report()

        elif choice == "14":
            safe_cleanup()

        elif choice == "0":

            print(
                "\nEXCORA System Manager closed."
            )

            break

        else:

            print(
                "\nInvalid option."
            )


# ============================================================
# MAIN
# ============================================================

def main():

    if not ROOT.exists():

        print(
            "EXCORA root directory not found."
        )

        sys.exit(1)

    menu()


if __name__ == "__main__":
    main()
