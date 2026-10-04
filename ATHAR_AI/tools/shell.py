import subprocess

from config import ALLOW_SHELL


def run_command(command):

    if not ALLOW_SHELL:
        return {
            "success": False,
            "error": "تنفيذ أوامر النظام معطل في الإعدادات."
        }

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc)
        }
