"""
main.py
Step 9: The final orchestration script.
1. Runs the Telegram Fetcher to grab the absolute latest data.
2. Launches the Flask Web Dashboard.
"""

import os
import asyncio
import threading
from telegram_fetcher import main as fetch_main
from app import app

def start_server():
    print("\n🌐 Starting Reflect AI Dashboard on http://localhost:5000 ...\n")
    # Turn off reloader to avoid running the fetcher twice
    app.run(host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    print("="*50)
    print(" Reflect AI — Social on Auto-Pilot Booting Up ")
    print("="*50)
    
    # 1. Fetch latest data first
    try:
        asyncio.run(fetch_main())
    except Exception as e:
        print(f"❌ Failed to fetch initial data: {e}")
        
    # 2. Start the web server
    start_server()
