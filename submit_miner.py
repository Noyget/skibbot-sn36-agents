#!/usr/bin/env python3
"""
Submit NOVA miner snapshot to Blueprint submission API.
Uses the wallet credentials from ~/.bittensor/wallets/biomedical_research
"""

import sys
import json
from pathlib import Path
from submission_uploader import submit_from_local_path

def main():
    # Configuration
    miner_path = Path.home() / ".openclaw/workspace/nova_ml_build"
    wallet_name = "biomedical_research"
    hotkey_name = "miner"
    submission_name = "nova-molecular-scout"
    
    print(f"📦 Submitting NOVA Miner Snapshot")
    print(f"━" * 60)
    print(f"Miner path: {miner_path}")
    print(f"Wallet: {wallet_name}")
    print(f"Hotkey: {hotkey_name}")
    print(f"Submission name: {submission_name}")
    print(f"━" * 60)
    
    # Check if miner directory exists
    if not miner_path.exists():
        print(f"❌ Error: Miner path does not exist: {miner_path}")
        sys.exit(1)
    
    # Check if miner.py exists
    miner_py = miner_path / "miner.py"
    if not miner_py.exists():
        print(f"❌ Error: miner.py not found at {miner_py}")
        sys.exit(1)
    
    print(f"✅ Miner path validated")
    print()
    
    # Submit
    print(f"🚀 Submitting to Blueprint API...")
    print()
    
    try:
        result = submit_from_local_path(
            local_path=str(miner_path),
            wallet_name=wallet_name,
            hotkey_name=hotkey_name,
            submission_name=submission_name,
        )
        
        print(f"Status Code: {result.status_code}")
        print(f"Success: {result.ok}")
        print(f"Request ID: {result.request_id}")
        print()
        
        if result.body:
            print(f"Response Body:")
            print(json.dumps(result.body, indent=2))
        else:
            print(f"Response Text:")
            print(result.text)
        
        print()
        if result.ok:
            print(f"✅ Submission successful!")
            print(f"Your miner snapshot is now in the Blueprint system.")
            print(f"Validators will pull and score it in the next cycle.")
            return 0
        else:
            print(f"❌ Submission failed (status {result.status_code})")
            return 1
            
    except Exception as e:
        print(f"❌ Error during submission: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
