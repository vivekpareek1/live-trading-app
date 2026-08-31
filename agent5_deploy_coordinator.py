import time
import subprocess
import os
from datetime import datetime

class Agent5_DeployCoordinator:
    def __init__(self):
        self.repo_path = "/home/ubuntu/live-trading-app"
        os.chdir(self.repo_path)
        
    def run_cmd(self, cmd, shell=False):
        try:
            if shell:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)

    def full_deploy(self):
        print(f"\n🚀 Agent5 - GitHub First PULL Mode - {datetime.now()}")
        print(f"Mode: Pull from GitHub -> Restart Services")
        
        print("\n[1/4] Git Pull from GitHub...")
        self.run_cmd(["git", "config", "user.email", "vivekpareek1@gmail.com"])
        self.run_cmd(["git", "config", "user.name", "Vivek Pareek"])
        self.run_cmd(["git", "config", "pull.rebase", "false"])
        
        success, out = self.run_cmd(["git", "fetch", "origin"])
        success, out = self.run_cmd(["git", "pull", "origin", "main"])
        print(f"Pull: {out[:500]}")
        git_ok = success
        
        print("\n[2/4] Restarting services...")
        for svc in ["trading-main", "trading-agent4", "trading-dashboard"]:
            self.run_cmd(["sudo", "systemctl", "restart", svc])
            time.sleep(2)
            s, o = self.run_cmd(["sudo", "systemctl", "is-active", svc])
            print(f"{svc}: {o.strip()}")
        
        print("\n[3/4] Fixing Dashboard...")
        self.run_cmd("pkill -f dashboard.py", shell=True)
        time.sleep(1)
        self.run_cmd("sudo fuser -k 5000/tcp", shell=True)
        time.sleep(1)
        s, o = self.run_cmd(["sudo", "systemctl", "is-active", "trading-dashboard"])
        if "active" not in o:
            print("Dashboard service down, manual start...")
            self.run_cmd("nohup python3 dashboard.py > dashboard.log 2>&1 &", shell=True)
            time.sleep(3)
        
        success, out = self.run_cmd(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:5000"])
        dashboard_ok = "200" in out
        print(f"Dashboard HTTP: {out} - OK={dashboard_ok}")
        
        success, out = self.run_cmd(["ps", "aux"])
        print(f"\n[4/4] Processes:")
        for line in out.split("\n"):
            if "python3" in line and ("main.py" in line or "agent4" in line or "dashboard" in line):
                print(line[:150])
        
        report = f"""
=== DEPLOY REPORT - {datetime.now()} ===
Mode: GitHub First -> AWS Pull Only
Git Pull: {"✅ SUCCESS" if git_ok else "❌ FAIL"}
Dashboard: {"✅ RUNNING" if dashboard_ok else "❌ DOWN - check dashboard.log"}
"""
        print(report)
        with open("deploy_report.txt", "w") as f:
            f.write(report)
        return git_ok

if __name__ == "__main__":
    agent = Agent5_DeployCoordinator()
    while True:
        try:
            agent.full_deploy()
        except Exception as e:
            print(f"Error: {e}")
        print("\nSleep 60 sec... GitHub First mode")
        time.sleep(60)
