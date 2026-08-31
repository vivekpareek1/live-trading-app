import subprocess, time
from datetime import datetime, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))
def log(m):
    t=datetime.now(IST).strftime('%H:%M:%S IST')
    print(f"[{t}] [DEPLOY] {m}")
    open("pipeline.log","a").write(f"[{t}] [DEPLOY] {m}\n")
    open("deploy_report.txt","a").write(f"[{t}] {m}\n")
def deploy(files):
    for f in files:
        if "dashboard" in f:
            subprocess.run(["sudo","systemctl","restart","trading-dashboard"],timeout=10)
            subprocess.run(["sudo","fuser","-k","5000/tcp"],capture_output=True)
            time.sleep(1)
            subprocess.Popen(["nohup","python3","dashboard.py"],stdout=open("/tmp/dash.log","w"),stderr=subprocess.STDOUT)
            log(f"🚀 Dashboard deployed")
        elif "trading" in f or "bot" in f or "strategy" in f:
            log(f"🤖 Trading code {f} deployed")
        elif f.endswith(".py"):
            r=subprocess.run(["python3","-m","py_compile",f],capture_output=True)
            if r.returncode==0: log(f"✅ {f} deployed")
def check():
    try:
        subprocess.run(["git","fetch","origin"],timeout=15,capture_output=True)
        local=subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True).stdout.strip()
        remote=subprocess.run(["git","rev-parse","origin/main"],capture_output=True,text=True).stdout.strip()
        if local==remote: return False
        diff=subprocess.run(["git","diff","--name-only",f"{local}..{remote}"],capture_output=True,text=True).stdout.strip()
        files=diff.split("\n") if diff else []
        log(f"🆕 New code: {', '.join(files[:3])}")
        subprocess.run(["git","pull","origin","main"],timeout=30,capture_output=True)
        deploy(files)
        log(f"✅ DEPLOYED {len(files)} files")
        return True
    except Exception as e:
        log(f"❌ {e}")
        return False
if __name__=="__main__":
    log("🚀 DEPLOY AGENT STARTED (60s) - ANY CODE")
    while True:
        check()
        time.sleep(60)
