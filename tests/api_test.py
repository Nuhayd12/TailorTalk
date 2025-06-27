import requests
import json
from datetime import datetime, timedelta

def test_api():
    """Test the TailorTalk API endpoints"""
    print("🚀 Testing TailorTalk API...")
    
    API_BASE = "http://localhost:8000"
    
    try:
        # Test 1: Health check
        print("\n📋 Step 1: Testing health endpoint...")
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check passed!")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Calendar Connected: {health_data.get('calendar_connected')}")
            print(f"   Agent Ready: {health_data.get('agent_ready')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test 2: Basic chat
        print("\n📋 Step 2: Testing chat endpoint...")
        chat_response = requests.post(
            f"{API_BASE}/chat",
            json={"message": "Hi, I want to schedule a meeting"},
            timeout=30
        )
        
        if chat_response.status_code == 200:
            chat_data = chat_response.json()
            print("✅ Chat endpoint working!")
            print(f"   Response: {chat_data.get('response')[:100]}...")
            print(f"   Session ID: {chat_data.get('session_id')[:12]}...")
            session_id = chat_data.get('session_id')
        else:
            print(f"❌ Chat failed: {chat_response.status_code}")
            print(f"   Error: {chat_response.text}")
            return False
        
        # Test 3: Follow-up message
        print("\n📋 Step 3: Testing conversation flow...")
        followup_response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Tomorrow at 2 PM for 1 hour", 
                "session_id": session_id
            },
            timeout=30
        )
        
        if followup_response.status_code == 200:
            followup_data = followup_response.json()
            print("✅ Conversation flow working!")
            print(f"   Response: {followup_data.get('response')[:100]}...")
            
            # Check if we got available slots
            available_slots = followup_data.get('available_slots', [])
            if available_slots:
                print(f"   Available slots found: {len(available_slots)}")
            else:
                print("   No slots returned yet (normal in conversation flow)")
        else:
            print(f"❌ Follow-up failed: {followup_response.status_code}")
        
        # Test 4: Availability endpoint
        print("\n📋 Step 4: Testing availability endpoint...")
        start_date = datetime.now().isoformat()
        end_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        avail_response = requests.get(
            f"{API_BASE}/availability",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "duration_minutes": 60
            },
            timeout=30
        )
        
        if avail_response.status_code == 200:
            avail_data = avail_response.json()
            slots = avail_data.get('available_slots', [])
            print("✅ Availability endpoint working!")
            print(f"   Found {len(slots)} available slots")
            if slots:
                print(f"   First slot: {slots[0].get('start', 'N/A')}")
        else:
            print(f"❌ Availability check failed: {avail_response.status_code}")
        
        print("\n🎉 API tests completed!")
        print("📋 Next step: Start the Streamlit frontend!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API - is the backend running?")
        print("💡 Start it with: python backend/api/main.py")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_api()