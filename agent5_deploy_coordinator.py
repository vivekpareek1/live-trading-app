
# AGENT 5 - PRE-CONFIGURED FOR VIVEK
# GitHub: https://github.com/vivekpareek1/live-trading-app
# AWS: 13.203.203.170
# Key: Khushi@1310 -> rename to Khushi1310.pem

import subprocess, time, json
from datetime import datetime
import os

class Agent5_DeployCoordinator:
    def __init__(self):
        self.github_repo = "https://github.com/vivekpareek1/live-trading-app.git"
        self.aws_ip = "13.203.203.170"
        self.aws_key = "./Khushi1310.pem"  # Rename your key file!
        self.status = {}
    
    def check_key(self):
        # Key file name me @ hai - rename karna better hai
        if not os.path.exists(self.aws_key):
            print(f"WARNING: Key file {self.aws_key} nahi mila")
            print(f"Tumhari file Khushi@1310 hai - isko rename karo:")
            print(f"mv 'Khushi@1310' Khushi1310.pem")
            print(f"chmod 400 Khushi1310.pem")
            return False
        return True

    def git_upload(self, msg="Deploy by Agent5"):
        print(f"[{datetime.now()}] Git Upload to https://github.com/vivekpareek1/live-trading-app...")
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", msg], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            self.status["git"] = "SUCCESS"
            print("✅ Git Upload SUCCESS")
            return True
        except Exception as e:
            print(f"❌ Git FAIL: {e}")
            self.status["git"] = str(e)
            return False
    
    def aws_deploy(self):
        print(f"[{datetime.now()}] AWS Deploy to {self.aws_ip} - Ports 22,8000,500 open")
        if not self.check_key():
            return False
        try:
            ssh_base = f"ssh -i {self.aws_key} -o StrictHostKeyChecking=no ubuntu@{self.aws_ip}"
            aws_cmd = f"""
            cd ~/live-trading-app 2>/dev/null || git clone https://github.com/vivekpareek1/live-trading-app.git ~/live-trading-app
            cd ~/live-trading-app
            git pull origin main
            pip3 install -r requirements.txt -q
            pkill -f agent4_FINAL_ADAPTIVE.py; pkill -f main.py; sleep 2
            chmod +x deploy.sh
            nohup python3 agent4_FINAL_ADAPTIVE.py > agent4.log 2>&1 &
            nohup python3 main.py > live.log 2>&1 &
            sleep 3
            echo "DEPLOYED_SUCCESS"
            ps aux | grep python | grep -v grep
            """
            full = f'{ssh_base} "{aws_cmd}"'
            result = subprocess.run(full, shell=True, capture_output=True, text=True, timeout=90)
            print(result.stdout)
            if "DEPLOYED_SUCCESS" in result.stdout:
                self.status["aws"] = "SUCCESS"
                print("✅ AWS Deploy SUCCESS")
                return True
            else:
                print(f"❌ AWS FAIL: {result.stderr}")
                self.status["aws"] = result.stderr
                return False
        except Exception as e:
            print(f"❌ AWS FAIL: {e}")
            self.status["aws"] = str(e)
            return False

    def test(self):
        print(f"[{datetime.now()}] Testing on {self.aws_ip}...")
        try:
            ssh = f"ssh -i {self.aws_key} ubuntu@{self.aws_ip}"
            cmd = f'{ssh} "cd ~/live-trading-app && cat agent4_adaptive_result.json 2>/dev/null; echo ---LOGS---; tail -10 live.log; tail -10 agent4.log"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            print(result.stdout)
            if "agent4" in result.stdout.lower() or "market" in result.stdout.lower():
                self.status["test"] = "SUCCESS"
                print("✅ Test SUCCESS")
                return True
            else:
                self.status["test"] = "FAIL"
                return False
        except Exception as e:
            self.status["test"] = str(e)
            return False

    def full_deploy(self):
        print("\n🚀 FULL AUTO DEPLOY - vivekpareek1/live-trading-app -> 13.203.203.170")
        print("Ports: 22 (SSH), 8000, 500 open\n")
        g = self.git_upload()
        time.sleep(2)
        a = self.aws_deploy() if g else False
        time.sleep(5)
        t = self.test() if a else False
        
        report = f"""
=== DEPLOY REPORT - {datetime.now()} ===
Repo: https://github.com/vivekpareek1/live-trading-app
AWS: 13.203.203.170
Ports: 22, 8000, 500
Git: {'✅' if g else '❌'} {self.status.get('git','')}
AWS: {'✅' if a else '❌'} {self.status.get('aws','')}
Test: {'✅' if t else '❌'} {self.status.get('test','')}

Check live: ssh -i Khushi1310.pem ubuntu@13.203.203.170 "tail -f ~/live-trading-app/agent4.log"
"""
        print(report)
        with open("deploy_report.txt", "w") as f:
            f.write(report)
        return g and a and t

if __name__ == "__main__":
    agent = Agent5_DeployCoordinator()
    agent.full_deploy()
