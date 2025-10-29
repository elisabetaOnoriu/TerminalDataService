import subprocess, sys

def spayn(process_type: str, concurrency: int = 4):
    cmd = [
        sys.executable, "-m", "celery",
        "-A", "app.celery_service.task:celery",
        process_type, "-l", "INFO"
    ]

    if process_type == "worker":
        cmd += ["--concurrency", str(concurrency)]

    return subprocess.Popen(cmd)