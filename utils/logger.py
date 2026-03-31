# utils/logger.py
import sys

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def banner():
    print(r"""
    ____                 ____      
   / __ \____  ___  ____  / __ \___  _________  ___
  / / / / __ \/ _ \/ __ \/ /_/ / _ \/ ___/ __ \/ _ \
 / /_/ / /_/ /  __/ / / / _, _/  __/ /__/ /_/ /  __/
 \____/ .___/\___/_/ /_/_/ |_|\___/\___/\____/\___/
     /_
""")

def info(msg): print(f"{Colors.OKCYAN}[INFO]{Colors.ENDC} {msg}")
def loading(msg): print(f"{Colors.OKBLUE}[~]{Colors.ENDC} {msg}")
def success(msg): print(f"{Colors.OKGREEN}[SUCCESS]{Colors.ENDC} {msg}")
def warning(msg): print(f"{Colors.WARNING}[WARNING]{Colors.ENDC} {msg}")
def error(msg): print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {msg}")
def critical(msg): print(f"{Colors.FAIL}{Colors.BOLD}[CRITICAL]{Colors.ENDC} {msg}")
def section(title): print(f"\n{Colors.HEADER}{Colors.BOLD}[--- {title} ---]{Colors.ENDC}")
def summary(data_dict):
    print(f"\n{Colors.OKGREEN}=== SUMMARY ==={Colors.ENDC}")
    if isinstance(data_dict, dict):
        for k, v in data_dict.items(): print(f"{k}: {v}")