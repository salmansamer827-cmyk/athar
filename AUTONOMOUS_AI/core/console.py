from datetime import datetime


def log(message, level="INFO"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] [{level}] {message}", flush=True)


def banner():
    print()
    print("=" * 60)
    print("        AUTONOMOUS AI - MASTER AGENT")
    print("=" * 60)
    print()
