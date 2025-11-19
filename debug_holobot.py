#!/usr/bin/env python3
"""
Debug script to test HoloBot connection
"""

import os
from dotenv import load_dotenv
from holobot import HoloBot
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_holobot():
    print("🔍 Testing HoloBot connection...")
    
    # Load environment
    load_dotenv()
    print(f"OLLAMA_URL: {os.getenv('OLLAMA_URL', 'http://localhost:11434')}")
    print(f"OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL', 'llama3.2:3b')}")
    
    try:
        # Initialize HoloBot
        print("\n📱 Initializing HoloBot...")
        bot = HoloBot()
        print("✅ HoloBot initialized successfully!")
        
        # Test direct API call first
        print("\n🔗 Testing direct Ollama API...")
        import requests
        try:
            test_response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:3b",
                    "prompt": "Hello",
                    "stream": False
                },
                timeout=5
            )
            print(f"Direct API Status: {test_response.status_code}")
            if test_response.status_code == 200:
                result = test_response.json()
                print(f"Direct API Response: {result.get('response', 'No response')[:100]}...")
            else:
                print(f"Direct API Error: {test_response.text}")
        except Exception as e:
            print(f"Direct API Failed: {e}")
        
        # Test AI response
        print("\n🧠 Testing HoloBot AI response...")
        test_message = "Hello"
        print(f"Sending message: {test_message}")
        
        import time
        start_time = time.time()
        try:
            response = bot.get_ai_response(test_message)
            end_time = time.time()
            print(f"✅ Response received in {end_time - start_time:.2f} seconds")
            print(f"Response: {response}")
        except Exception as e:
            print(f"❌ HoloBot response failed: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_holobot()
