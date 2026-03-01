import requests
import time
import json
import base64

BASE_URL = "http://localhost:8000"

def run_tests():
    print("Starting Agent API Tests...")
    
    # 1. Login to get token
    print("\n[1] Logging in...")
    login_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    
    # Let's try to register first just in case
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword",
        "full_name": "Test User"
    })
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return
        
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")

    agents = [
        "wellbeing",
        "diagnostic",
        "virtual_doctor",
        "dietary",
        "insurance",
        "visualisation",
        "orchestrator"
    ]

    for agent in agents:
        print(f"\n[{agent.upper()}] Testing Agent API...")
        
        # Create session
        session_resp = requests.post(
            f"{BASE_URL}/sessions",
            json={"agent_type": agent},
            headers=headers
        )
        
        if session_resp.status_code != 201:
            print(f"❌ Failed to create session for {agent}: {session_resp.status_code} - {session_resp.text}")
            continue
            
        session_id = session_resp.json().get("id")
        print(f"  ✅ Session created: {session_id}")
        
        # Send chat message
        chat_payload = {
            "session_id": session_id,
            "message": "Hello, this is an automated functional test. Please respond with a short confirmation message."
        }
        print(f"  -> Sending message...")
        start_time = time.time()
        
        chat_resp = requests.post(
            f"{BASE_URL}/agents/{agent}/chat",
            json=chat_payload,
            headers=headers
        )
        
        elapsed = time.time() - start_time
        
        if chat_resp.status_code == 200:
            resp_data = chat_resp.json()
            reply_text = resp_data.get('reply') or resp_data.get('response') or str(resp_data)
            print(f"  ✅ Chat successful ({elapsed:.2f}s)")
            print(f"  -> Response: {reply_text[:100]}...")
        else:
            print(f"  ❌ Chat failed: {chat_resp.status_code} - {chat_resp.text}")

if __name__ == "__main__":
    run_tests()
