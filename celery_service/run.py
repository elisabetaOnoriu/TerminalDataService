import subprocess, sys

def start_worker():
    return subprocess.Popen(
        [sys.executable, "-m", "celery", "-A", "celery_service.task:celery",
         "worker", "-l", "INFO", "--concurrency", "4"]
    )

def start_beat():
    return subprocess.Popen(
        [sys.executable, "-m", "celery", "-A", "celery_service.task:celery",
         "beat", "-l", "INFO"]
    )
