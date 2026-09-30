#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()

# ============================================================
# EXCORA SYSTEM CONTROL V3
# ============================================================

VERSION = "3.0"

PROTECTED_PATHS = [
    HOME / "EXCORA",
    HOME / "EXCORA_V10",
    HOME / "capital-wise",
    HOME / "valora",
    HOME / "downloads",
]

SAFE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}

SAFE_FILE_SUFFIXES = {
    ".pyc",
    ".pyo",
}

LOG_SUFFIXES = {
    ".log",
    ".tmp",
    ".temp",
}

MAX_PREVIEW = 100


# ============================================================
# UI
# ============================================================

def header(title: str):
    print("\n" + "=" * 64)
    print(f"EXCORA SYSTEM CONTROL V{VERSION}")
    print(title)
    print("=" * 64)


def pause():
    input("\nPress ENTER to continue...")


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} PB"


# ============================================================
# SECURITY
# ============================================================

def real_path(path: Path) -> Path:
    try:
        return path.resolve(strict=False)
    except Exception:
        return Path(os.path.abspath(path))


def is_protected(path: Path) -> bool:
    target = real_path(path)

    for protected in PROTECTED_PATHS:
        protected_real = real_path(protected)

        if target == protected_real:
            return True

        try:
            target.relative_to(protected_real)
            return True
        except ValueError:
            pass

    return False


def safe_delete_allowed(path: Path) -> bool:
    if is_protected(path):
        print(f"[BLOCKED] Protected: {path}")
        return False

    if not path.exists() and not path.is_symlink():
        return False

    if path.is_symlink():
        print(f"[BLOCKED] Symlink: {path}")
        return False

    return True


# ============================================================
# STORAGE
# ============================================================

def directory_size(path: Path) -> int:
    total = 0

    if not path.exists():
        return 0

    try:
        for root, dirs, files in os.walk(path, followlinks=False):
            dirs[:] = [
                d for d in dirs
                if not (Path(root) / d).is_symlink()
            ]

            for name in files:
                p = Path(root) / name
                try:
                    if not p.is_symlink():
                        total += p.stat().st_size
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass

    return total


def storage_overview():
    header("STORAGE OVERVIEW")

    try:
        usage = shutil.disk_usage(HOME)
        print(f"Total      : {human_size(usage.total)}")
        print(f"Used       : {human_size(usage.used)}")
        print(f"Free       : {human_size(usage.free)}")
        print(f"Used       : {usage.used / usage.total * 100:.1f}%")
    except Exception as e:
        print(f"Unable to read storage: {e}")

    print(f"\nHome       : {human_size(directory_size(HOME))}")


def largest_directories():
    header("LARGEST HOME DIRECTORIES")

    results = []

    try:
        for item in HOME.iterdir():
            if item.is_dir() and not item.is_symlink():
                try:
                    size = directory_size(item)
                    results.append((size, item))
                except Exception:
                    pass
    except Exception as e:
        print(e)
        return

    results.sort(reverse=True, key=lambda x: x[0])

    for size, path in results[:30]:
        print(f"{human_size(size):>12}  {path}")


def largest_files():
    header("LARGEST FILES")

    results = []

    for root, dirs, files in os.walk(HOME, followlinks=False):
        dirs[:] = [
            d for d in dirs
            if not (Path(root) / d).is_symlink()
        ]

        for name in files:
            path = Path(root) / name

            try:
                if path.is_symlink():
                    continue

                size = path.stat().st_size
                results.append((size, path))

            except (OSError, PermissionError):
                pass

    results.sort(reverse=True, key=lambda x: x[0])

    for size, path in results[:50]:
        print(f"{human_size(size):>12}  {path}")


# ============================================================
# CLEANUP DISCOVERY
# ============================================================

def find_python_cache():
    found = []

    for root, dirs, files in os.walk(HOME, followlinks=False):
        dirs[:] = [
            d for d in dirs
            if not (Path(root) / d).is_symlink()
        ]

        for d in list(dirs):
            path = Path(root) / d

            if d in SAFE_DIR_NAMES:
                found.append(path)

        for name in files:
            path = Path(root) / name

            if path.suffix.lower() in SAFE_FILE_SUFFIXES:
                found.append(path)

    return found


def find_temp_logs():
    found = []

    for root, dirs, files in os.walk(HOME, followlinks=False):
        dirs[:] = [
            d for d in dirs
            if not (Path(root) / d).is_symlink()
        ]

        for name in files:
            path = Path(root) / name

            if path.suffix.lower() in LOG_SUFFIXES:
                if not is_protected(path):
                    found.append(path)

    return found


def pip_cache_size() -> int:
    cache = HOME / ".cache" / "pip"
    return directory_size(cache)


def npm_cache_size() -> int:
    try:
        result = subprocess.run(
            ["npm", "cache", "verify"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        text = result.stdout + result.stderr

        # npm output differs between versions.
        # We don't parse it for deletion decisions.
        return directory_size(HOME / ".npm")

    except Exception:
        return directory_size(HOME / ".npm")


def cargo_size() -> int:
    return directory_size(HOME / ".cargo")


def cleanup_candidates():
    candidates = []

    candidates.extend(find_python_cache())
    candidates.extend(find_temp_logs())

    pip_cache = HOME / ".cache" / "pip"
    if pip_cache.exists():
        candidates.append(pip_cache)

    npm_cache = HOME / ".npm"
    if npm_cache.exists():
        candidates.append(npm_cache)

    return list(dict.fromkeys(candidates))


# ============================================================
# PREVIEW
# ============================================================

def preview_candidates(candidates):
    header("CLEANUP PREVIEW")

    total = 0
    valid = []

    for path in candidates:
        if is_protected(path):
            continue

        if not path.exists():
            continue

        try:
            size = (
                directory_size(path)
                if path.is_dir()
                else path.stat().st_size
            )

            total += size
            valid.append((size, path))

        except (OSError, PermissionError):
            pass

    valid.sort(reverse=True, key=lambda x: x[0])

    print(f"Items          : {len(valid)}")
    print(f"Recoverable    : {human_size(total)}")
    print()

    for size, path in valid[:MAX_PREVIEW]:
        print(f"{human_size(size):>12}  {path}")

    if len(valid) > MAX_PREVIEW:
        print(f"\n... and {len(valid) - MAX_PREVIEW} more")

    return valid, total


# ============================================================
# DELETE
# ============================================================

def remove_path(path: Path) -> bool:
    if not safe_delete_allowed(path):
        return False

    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

        return True

    except Exception as e:
        print(f"[FAILED] {path}: {e}")
        return False


def safe_clean():
    candidates = cleanup_candidates()

    valid, total = preview_candidates(candidates)

    if not valid:
        print("\nNothing safe to clean.")
        return

    print(f"\nPotential recovery: {human_size(total)}")

    answer = input("\nDelete SAFE items? [y/N]: ").strip().lower()

    if answer != "y":
        print("Cancelled.")
        return

    before = directory_size(HOME)

    success = 0

    for _, path in valid:
        if remove_path(path):
            print(f"[OK] {path}")
            success += 1

    after = directory_size(HOME)

    print("\n" + "-" * 64)
    print("CLEANUP REPORT")
    print("-" * 64)
    print(f"Items removed : {success}")
    print(f"Before        : {human_size(before)}")
    print(f"After         : {human_size(after)}")

    if before > after:
        print(f"Recovered     : {human_size(before - after)}")
    else:
        print("Recovered     : 0 B")


# ============================================================
# CACHE MANAGER
# ============================================================

def cache_manager():
    header("CACHE MANAGER")

    print(f"PIP cache       : {human_size(pip_cache_size())}")
    print(f"NPM cache       : {human_size(npm_cache_size())}")
    print(f"Cargo           : {human_size(cargo_size())}")

    print("\n1  PIP cache cleanup")
    print("2  NPM cache cleanup")
    print("3  Cargo analysis")
    print("0  Back")

    choice = input("\nCACHE > ").strip()

    if choice == "1":
        answer = input("Run pip cache purge? [y/N]: ").strip().lower()

        if answer == "y":
            subprocess.run([sys.executable, "-m", "pip", "cache", "purge"])

    elif choice == "2":
        answer = input("Run npm cache clean --force? [y/N]: ").strip().lower()

        if answer == "y":
            subprocess.run(["npm", "cache", "clean", "--force"])

    elif choice == "3":
        cargo_manager()


# ============================================================
# DEVELOPMENT
# ============================================================

def venv_manager():
    header("PYTHON / VENV MANAGER")

    candidates = [
        HOME / "venv",
        HOME / "EXCORA_V10" / "venv",
        HOME / "capital-wise" / ".venv",
        HOME / "valora" / ".venv",
    ]

    for path in candidates:
        if path.exists():
            print(f"{human_size(directory_size(path)):>12}  {path}")
        else:
            print(f"{'MISSING':>12}  {path}")

    print("\nVENV deletion is disabled in this V3 safe manager.")
    print("Use the manual project workflow after reviewing dependencies.")


def pip_manager():
    header("PIP MANAGER")

    subprocess.run([sys.executable, "-m", "pip", "cache", "info"])


def npm_manager():
    header("NPM MANAGER")

    subprocess.run(["npm", "--version"])
    print(f"NPM home cache: {human_size(directory_size(HOME / '.npm'))}")


def cargo_manager():
    header("CARGO MANAGER")

    cargo = HOME / ".cargo"

    print(f"Total Cargo         : {human_size(directory_size(cargo))}")
    print(f"Registry            : {human_size(directory_size(cargo / 'registry'))}")
    print(f"Registry cache      : {human_size(directory_size(cargo / 'registry' / 'cache'))}")
    print(f"Registry source     : {human_size(directory_size(cargo / 'registry' / 'src'))}")

    print("\nCargo deletion is REVIEW ONLY in V3.")
    print("Toolchains are protected from automatic deletion.")


# ============================================================
# PROJECTS
# ============================================================

def project_manager():
    header("PROJECT MANAGER")

    projects = [
        ("EXCORA", HOME / "EXCORA"),
        ("EXCORA_V10", HOME / "EXCORA_V10"),
        ("CAPITAL WISE", HOME / "capital-wise"),
        ("VALORA", HOME / "valora"),
        ("DOWNLOADS", HOME / "downloads"),
    ]

    for name, path in projects:
        if path.exists():
            print(f"{name:<16} {human_size(directory_size(path)):>12}")
        else:
            print(f"{name:<16} MISSING")


def project_cache_cleanup():
    header("PROJECT CACHE CLEANUP")

    candidates = []

    for project in [
        HOME / "EXCORA",
        HOME / "EXCORA_V10",
        HOME / "capital-wise",
        HOME / "valora",
    ]:
        if project.exists():
            candidates.extend(
                p for p in find_python_cache()
                if p.is_relative_to(project)
            )

    valid, total = preview_candidates(candidates)

    if not valid:
        print("No project caches found.")
        return

    print(f"\nRecoverable project cache: {human_size(total)}")

    answer = input("Delete these cache files? [y/N]: ").strip().lower()

    if answer != "y":
        print("Cancelled.")
        return

    for _, path in valid:
        remove_path(path)

    print("Project cache cleanup completed.")


# ============================================================
# ANDROID
# ============================================================

def adb_available():
    return shutil.which("pm") is not None or shutil.which("cmd") is not None


def android_apps():
    header("ANDROID APP MANAGER")

    print("1  List installed packages")
    print("2  Search package")
    print("3  App information")
    print("4  Uninstall user app")
    print("5  Disable app")
    print("0  Back")

    choice = input("\nANDROID > ").strip()

    if choice == "1":
        subprocess.run(["pm", "list", "packages"])

    elif choice == "2":
        query = input("Search: ").strip()

        if query:
            result = subprocess.run(
                ["pm", "list", "packages"],
                capture_output=True,
                text=True,
            )

            for line in result.stdout.splitlines():
                if query.lower() in line.lower():
                    print(line)

    elif choice == "3":
        package = input("Package name: ").strip()

        if package:
            subprocess.run(["dumpsys", "package", package])

    elif choice == "4":
        package = input("USER APP package: ").strip()

        if not package:
            return

        if package in {
            "com.termux",
            "com.android.systemui",
            "android",
        }:
            print("[BLOCKED] Critical package.")
            return

        answer = input(
            f"Uninstall {package} for current user? [y/N]: "
        ).strip().lower()

        if answer == "y":
            subprocess.run(
                ["pm", "uninstall", "--user", "0", package]
            )

    elif choice == "5":
        package = input("Package name: ").strip()

        if package:
            answer = input(
                f"Disable {package}? [y/N]: "
            ).strip().lower()

            if answer == "y":
                subprocess.run(
                    ["pm", "disable-user", "--user", "0", package]
                )


# ============================================================
# LARGE FILES
# ============================================================

def large_files():
    header("LARGE FILE SCANNER")

    minimum_mb = input(
        "Minimum size MB [default 50]: "
    ).strip()

    try:
        minimum = float(minimum_mb or "50")
    except ValueError:
        minimum = 50

    minimum_bytes = int(minimum * 1024 * 1024)

    results = []

    for root, dirs, files in os.walk(HOME, followlinks=False):
        dirs[:] = [
            d for d in dirs
            if not (Path(root) / d).is_symlink()
        ]

        for name in files:
            path = Path(root) / name

            try:
                if path.is_symlink():
                    continue

                size = path.stat().st_size

                if size >= minimum_bytes:
                    results.append((size, path))

            except (OSError, PermissionError):
                pass

    results.sort(reverse=True, key=lambda x: x[0])

    for size, path in results[:100]:
        status = "PROTECTED" if is_protected(path) else "REVIEW"

        print(
            f"{human_size(size):>12}  "
            f"[{status:<9}] {path}"
        )


# ============================================================
# SYSTEM
# ============================================================

def system_information():
    header("SYSTEM INFORMATION")

    commands = [
        ["uname", "-a"],
        [sys.executable, "--version"],
        ["node", "--version"],
        ["npm", "--version"],
        ["cargo", "--version"],
    ]

    for command in commands:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10,
            )

            print(result.stdout.strip() or result.stderr.strip())

        except Exception as e:
            print(f"{command[0]}: unavailable ({e})")


def protected_paths():
    header("PROTECTED PATHS")

    for path in PROTECTED_PATHS:
        print(f"[PROTECTED] {path}")


def full_diagnostic():
    storage_overview()
    largest_directories()
    project_manager()
    system_information()

    print("\nProtected paths:")
    protected_paths()


# ============================================================
# MAIN MENU
# ============================================================

def menu():
    while True:

        print(
            """
╔══════════════════════════════════════════════════════╗
║          EXCORA SYSTEM CONTROL V3                  ║
╠══════════════════════════════════════════════════════╣
║ STORAGE                                              ║
║  1  Storage Overview                                 ║
║  2  Largest Directories                              ║
║  3  Largest Files                                    ║
║  4  Duplicate Scanner                                ║
║                                                      ║
║ CLEANUP                                              ║
║  5  Cleanup Preview                                  ║
║  6  Safe Clean                                       ║
║  7  Smart Clean                                      ║
║  8  Deep Clean                                       ║
║  9  Cache Manager                                    ║
║                                                      ║
║ DEVELOPMENT                                          ║
║ 10  Python / VENV Manager                            ║
║ 11  PIP Manager                                      ║
║ 12  NPM Manager                                      ║
║ 13  Cargo Manager                                    ║
║                                                      ║
║ PROJECTS                                             ║
║ 14  Project Manager                                  ║
║ 15  Project Storage                                  ║
║ 16  Project Cache Cleanup                            ║
║                                                      ║
║ ANDROID                                              ║
║ 17  Android App Manager                              ║
║                                                      ║
║ SYSTEM                                               ║
║ 18  System Information                               ║
║ 19  Full Diagnostic                                  ║
║ 20  Protected Paths                                  ║
║                                                      ║
║  0  Exit                                             ║
╚══════════════════════════════════════════════════════╝
"""
        )

        choice = input("\nEXCORA > ").strip()

        try:
            if choice == "1":
                storage_overview()
                pause()

            elif choice == "2":
                largest_directories()
                pause()

            elif choice == "3":
                largest_files()
                pause()

            elif choice == "4":
                print("\nDuplicate scanner will be enabled in V3.1.")
                pause()

            elif choice == "5":
                preview_candidates(cleanup_candidates())
                pause()

            elif choice == "6":
                safe_clean()
                pause()

            elif choice == "7":
                print("\nSMART CLEAN")
                print("Analyze safe/review/protected categories.")
                preview_candidates(cleanup_candidates())
                pause()

            elif choice == "8":
                print("\nDEEP CLEAN is REVIEW ONLY.")
                print("No destructive deep cleanup is executed automatically.")
                cargo_manager()
                pause()

            elif choice == "9":
                cache_manager()
                pause()

            elif choice == "10":
                venv_manager()
                pause()

            elif choice == "11":
                pip_manager()
                pause()

            elif choice == "12":
                npm_manager()
                pause()

            elif choice == "13":
                cargo_manager()
                pause()

            elif choice == "14":
                project_manager()
                pause()

            elif choice == "15":
                project_manager()
                pause()

            elif choice == "16":
                project_cache_cleanup()
                pause()

            elif choice == "17":
                android_apps()
                pause()

            elif choice == "18":
                system_information()
                pause()

            elif choice == "19":
                full_diagnostic()
                pause()

            elif choice == "20":
                protected_paths()
                pause()

            elif choice == "0":
                print("\nEXCORA SYSTEM CONTROL: EXIT")
                break

            else:
                print("Invalid option.")

        except KeyboardInterrupt:
            print("\n\nInterrupted safely.")
            continue

        except Exception as e:
            print(f"\n[ERROR] {e}")
            pause()


def main():
    menu()


if __name__ == "__main__":
    main()
