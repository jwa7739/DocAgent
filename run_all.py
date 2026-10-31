import subprocess
import sys
import time
import urllib.request

API_HEALTH = "http://127.0.0.1:8000/health"


def wait_for_api(timeout: int = 180) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(API_HEALTH, timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(1)
    return False


def main():
    api = subprocess.Popen([sys.executable, "main.py"])
    ui = None
    try:
        print("⏳ Waiting for the API to start...")
        if not wait_for_api():
            print("❌ API did not start - check the error above.")
            return
        ui = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])
        ui.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        for p in (ui, api):
            if p and p.poll() is None:
                p.terminate()


if __name__ == "__main__":
    main()
