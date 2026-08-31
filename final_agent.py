import os, time, shutil, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
IST = timezone(timedelta(hours=5, minutes=30))

def log(m):
    t=datetime.now(IST).strftime('%H:%M:%S IST')
    print(f"[{t}] {m}")
    open("pipeline.log","a").write(f"[{t}] {m}\n")

def deploy_file(f):
    name = Path(f).name
    log(f"Deploying {name}")
    if "dashboard" in name:
        # Backup and deploy
        if Path("dashboard.py").exists():
            shutil.copy("dashboard.py", "dashboard.py.bak")
        shutil.copy(f, "dashboard.py")
        # Syntax check
        r=subprocess.run(["python3","-m","py_compile","dashboard.py"],capture_output=True)
        if r.returncode==0:
            subprocess.Popen(["nohup","python3","dashboard.py"],stdout=open("/tmp/final.log","w"),stderr=subprocess.STDOUT)
            log(f"✅ Dashboard LIVE - {name}")
        else:
            log(f"❌ Syntax error {name}")
            shutil.copy("dashboard.py.bak", "dashboard.py")

    elif name.endswith(".py"):
        shutil.copy(f, Path(f).name)
        r=subprocess.run(["python3","-m","py_compile",Path(f).name],capture_output=True)
        if r.returncode==0:
            log(f"✅ {name} deployed")
        else:
            log(f"❌ {name} syntax error")

    # Try GitHub push if remote exists
    try:
        subprocess.run(["git","add","."],timeout=5,capture_output=True)
        subprocess.run(["git","commit","-m",f"Auto {datetime.now(IST).strftime('%H:%M')}"],timeout=5,capture_output=True)
        subprocess.run(["git","push","origin","main"],timeout=10,capture_output=True)
    except:
        pass # GitHub nahi hai to bhi chalega

if __name__=="__main__":
    Path("incoming_changes").mkdir(exist_ok=True)
    Path("pipeline.log").touch(exist_ok=True)
    log("🚀 FINAL AGENT STARTED - Har 30 sec check, GitHub optional")

    # Initial dashboard - IST fixed
    dashboard_code = '''
from flask import Flask
from datetime import datetime, timezone, timedelta
app = Flask(__name__)
IST = timezone(timedelta(hours=5, minutes=30))
@app.route("/")
def home():
    ist=datetime.now(IST).strftime('%d-%m-%Y %H:%M:%S IST')
    return f"<html><body style='background:#000;color:#0f0;padding:20px;font-family:monospace'><h1>✅ FINAL AGENT LIVE</h1><h2>{ist}</h2><p>IST Fixed - UTC+5:30</p><p>Pipeline: Meta AI -> incoming_changes/ -> Agent (30s) -> Live</p><p>No GitHub needed, direct deploy</p><p>Time: {ist}</p></body></html>"
if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)
'''
    open("incoming_changes/dashboard.py","w").write(dashboard_code)

    while True:
        # Check incoming_changes folder
        inc=Path("incoming_changes")
        files=list(inc.glob("*"))
        for file in files:
            if file.is_file():
                deploy_file(file)
                file.unlink()

        # Also check direct git pull if remote exists
        try:
            subprocess.run(["git","fetch","origin"],timeout=10,capture_output=True)
            local=subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True).stdout.strip()
            remote=subprocess.run(["git","rev-parse","origin/main"],capture_output=True,text=True).stdout.strip()
            if local!=remote and local and remote:
                log(f"🆕 GitHub new code found")
                subprocess.run(["git","pull","origin","main"],timeout=20,capture_output=True)
                if Path("dashboard.py").exists():
                    subprocess.Popen(["nohup","python3","dashboard.py"],stdout=open("/tmp/final.log","w"),stderr=subprocess.STDOUT)
                    log("✅ Deployed from GitHub")
        except:
            pass

        time.sleep(30)
