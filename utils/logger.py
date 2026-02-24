import sys
import time

def banner():
    print("""
   ____                  ____                      
  / __ \\____  ___  ____  / __ \\___  _________  ___ 
 / / / / __ \\/ _ \\/ __ \\/ /_/ / _ \\/ ___/ __ \\/ _ \\
/ /_/ / /_/ /  __/ / / / _, _/  __/ /__/ /_/ /  __/
\\____/ .___/\\___/_/ /_/_/ |_|\\___/\\___/\\____/\\___/ 
    /_/                                              
    """)

def section(name):
    print(f"\n{'='*10} {name} {'='*10}")

def info(message):
    print(f"[INFO] {message}")

def critical(message):
    print(f"[CRITICAL] {message}")

def success(message):
    print(f"[SUCCESS] {message}")

def warning(message):
    print(f"[WARNING] {message}")

def loading(message):
    sys.stdout.write(f"\r[~] {message}")
    sys.stdout.flush()
    time.sleep(0.2)

def summary(data):
    print("\n" + "="*30)
    print("SUMMARY")
    print("="*30)
    print(f"Links   : {len(data['links'])}")
    print(f"Emails  : {len(data['emails'])}")
    print(f"Phones  : {len(data['phones'])}")
    print(f"IPs     : {len(data['ips'])}")
    print("="*30)