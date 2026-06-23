import time
from dotenv import load_dotenv
load_dotenv()

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.tools.weekly_quiz import generate_weekly_quiz
from agent.tools.comms_tools import check_pending_approvals

def run_test():
    print("=========================================")
    print(" TESTING THE AGENTIC APPROVAL LOOP ")
    print("=========================================\n")
    
    print("[1/3] Generating a test quiz and sending the email...")
    print("      (If prompted, please authenticate in your browser to grant Drive + Gmail send access)")
    
    res = generate_weekly_quiz(standards=["6.EE.A.1"], title="End to End Approval Test")
    
    print("\nResult from generation:")
    print(res["message"])
    print("\n=========================================")
    print(" WAITING for 'Karrie' to respond...")
    print("=========================================")
    print("\nCheck the inbox for redacted@example.com!")
    print("1. Read the email from Nova.")
    print("2. Click the Drive link.")
    print("3. In Google Drive, move that file into the '02_Approved' folder.")
    print("4. Come back here and press ENTER.")
    
    input("\nPress Enter when Karrie has moved the file to 02_Approved...")
    
    print("\n[3/3] Checking for approvals...")
    check_res = check_pending_approvals()
    
    print("\nResult from check_pending_approvals():")
    print(check_res)
    
    print("\n=========================================")
    print(" TEST COMPLETE ")
    print("=========================================")

if __name__ == "__main__":
    run_test()
