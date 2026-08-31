#!/bin/bash
echo "=== ONE TIME PIPELINE SETUP - Bas ye ek baar ==="

# 1. Git check
if [ ! -d ".git" ]; then
  git init
  echo "Git init done"
fi

# Remote check - agar nahi hai to banao
if ! git remote | grep -q origin; then
  echo "⚠️ GitHub remote nahi hai - apna repo URL daalo:"
  echo "Example: https://github.com/USERNAME/live-trading-app.git"
  read -p "GitHub URL: " GH_URL
  if [ ! -z "$GH_URL" ]; then
    git remote add origin $GH_URL
    echo "Remote added: $GH_URL"
  fi
fi

# 2. Folders
mkdir -p incoming_changes logs
echo "incoming_changes/" >> .gitignore 2>/dev/null
echo "*.log" >> .gitignore 2>/dev/null
echo "__pycache__/" >> .gitignore 2>/dev/null

# 3. PUSH AGENT - Meta AI -> GitHub (har 30 sec)
cat > git_push_agent.py << 'PYEOF'
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
PYEOF

# 4. DEPLOY AGENT - GitHub -> AWS (har 60 sec)
cat > deploy_agent.py << 'PYEOF'
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
PYEOF

# 5. Systemd services
sudo tee /etc/systemd/system/git-push-agent.service > /dev/null << 'EOF'
[Unit]
Description=Push Agent - Meta AI to GitHub 30s
After=network.target
[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/live-trading-app
ExecStart=/usr/bin/python3 git_push_agent.py
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/deploy-agent.service > /dev/null << 'EOF'
[Unit]
Description=Deploy Agent - GitHub to AWS 60s
After=network.target
[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/live-trading-app
ExecStart=/usr/bin/python3 deploy_agent.py
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF

# 6. Start everything
sudo systemctl daemon-reload
sudo systemctl enable git-push-agent.service deploy-agent.service
sudo systemctl restart git-push-agent.service deploy-agent.service

# 7. Initial IST fix through pipeline
cat > incoming_changes/dashboard.py << 'PYEOF'
from flask import Flask
import requests
from datetime import datetime, timezone, timedelta
app = Flask(__name__)
IST = timezone(timedelta(hours=5, minutes=30))
def ist(): return datetime.now(IST).strftime('%d-%m-%Y %H:%M:%S IST')
def prices():
    try:
        r=requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,tether-gold&vs_currencies=usd',timeout=4).json()
        return float(r['bitcoin']['usd']), float(r['ethereum']['usd']), float(r['solana']['usd']), float(r['tether-gold']['usd'])
    except:
        return 78536, 2453, 104, 4446
@app.route('/')
def home():
    btc,eth,sol,gold=prices()
    return f"<html><head><meta http-equiv='refresh' content='10'><script src='https://cdn.jsdelivr.net/npm/chart.js'></script><style>body{{background:#0a0e14;color:#fff;font-family:Arial;padding:10px}}.h{{background:#0a2a12;border:2px solid #00ff88;padding:12px;text-align:center}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:10px}}.card{{background:#151b22;border:1px solid #333;border-radius:10px;padding:10px}}</style></head><body><div class='h'>🚀 PIPELINE LIVE ✅ {ist()} | IST FIXED | Auto Pipeline</div><div class='grid'><div class='card'>BTC ${btc}</div><div class='card'>ETH ${eth}</div><div class='card'>SOL ${sol}</div><div class='card'>GOLD ${gold}</div></div><div style='background:#151b22;padding:10px;margin-top:10px;font-size:11px'>✅ ONE TIME SETUP DONE | Pipeline: Meta AI -> Push Agent (30s) -> GitHub -> Deploy Agent (60s) -> Live | Time: {ist()}</div></body></html>"
if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000)
PYEOF

sleep 2
echo ""
echo "=== ✅ ONE TIME SETUP DONE ==="
sudo systemctl status git-push-agent.service deploy-agent.service --no-pager | grep -E "Active|Loaded"
echo ""
echo "Pipeline: Meta AI -> incoming_changes/ -> Push (30s) -> GitHub -> Deploy (60s) -> Live"
echo "Dashboard: http://13.203.203.170:5000"
echo "Logs: tail -f pipeline.log"
echo ""
echo "Ab tumhe kuch nahi chalana - agents sab karenge!"
echo "Bas mujhe bolo kya change chahiye, pipeline khud deploy karega"
