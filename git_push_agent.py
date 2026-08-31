import subprocess, time, shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
IST = timezone(timedelta(hours=5, minutes=30))
def log(m):
    t=datetime.now(IST).strftime('%H:%M:%S IST')
    print(f"[{t}] [PUSH] {m}")
    open("pipeline.log","a").write(f"[{t}] [PUSH] {m}\n")
def push():
    try:
        s=subprocess.run(["git","status","--porcelain"],capture_output=True,text=True).stdout.strip()
        if not s: return False
        log(f"Changes: {len(s.splitlines())} files")
        subprocess.run(["git","add","--all","--",":!*.log",":!__pycache__"],timeout=10)
        msg=f"Pipeline {datetime.now(IST).strftime('%d-%m %H:%M IST')}"
        subprocess.run(["git","commit","-m",msg],capture_output=True,timeout=10)
        r=subprocess.run(["git","push","origin","main"],capture_output=True,text=True,timeout=30)
        if r.returncode==0:
            log(f"✅ Pushed to GitHub")
            return True
        else:
            log(f"❌ Push fail: {r.stderr[:100]}")
            return False
    except Exception as e:
        log(f"❌ {e}")
        return False
def check_incoming():
    inc=Path("incoming_changes")
    inc.mkdir(exist_ok=True)
    files=list(inc.glob("*"))
    if not files: return False
    for f in files:
        if f.is_file():
            shutil.copy(f, Path(f.name))
            log(f"📥 {f.name} from Meta AI")
            f.unlink()
    push()
    return True
if __name__=="__main__":
    log("🚀 PUSH AGENT STARTED (30s)")
    while True:
        if not check_incoming(): push()
        time.sleep(30)
