#!/usr/bin/env python3
"""
Simple script to kill all voxtral tray processes
"""
import subprocess
import sys

def kill_all_tray_processes():
    """Kill all voxtral tray processes"""
    try:
        print("🔥 Killing all voxtral tray processes...")
        
        # Kill all voxtral processes
        result = subprocess.run(['pkill', '-9', '-f', 'voxtral_tray'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tray processes killed")
        else:
            print("⚠️ No tray processes found or already killed")
            
        # Verify they're gone
        check_result = subprocess.run(['pgrep', '-f', 'voxtral_tray'], 
                                    capture_output=True, text=True)
        
        if check_result.returncode != 0:
            print("✅ Confirmed: All tray processes are gone")
        else:
            print("⚠️ Some processes may still be running")
            
    except Exception as e:
        print(f"❌ Error killing processes: {e}")

if __name__ == "__main__":
    kill_all_tray_processes()