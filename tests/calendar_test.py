import sys
import os
# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Direct import from the google_calendar module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "google_calendar", 
    os.path.join(backend_path, "calendar", "google_calendar.py")
)
google_calendar_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(google_calendar_module)

GoogleCalendarService = google_calendar_module.GoogleCalendarService

from datetime import datetime, timedelta

def test_calendar_integration():
    """Test our Google Calendar integration"""
    print("🔍 Testing Google Calendar Integration...")
    
    # Initialize calendar service
    calendar_service = GoogleCalendarService()
    
    # Test authentication
    print("📋 Step 1: Testing authentication...")
    if calendar_service.authenticate():
        print("✅ Authentication successful!")
    else:
        print("❌ Authentication failed - check credentials.json")
        return False
    
    # Test availability check
    print("📋 Step 2: Testing availability check...")
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    try:
        busy_periods = calendar_service.get_availability(start_date, end_date)
        print(f"✅ Found {len(busy_periods)} busy periods")
    except Exception as e:
        print(f"❌ Availability check failed: {e}")
        return False
    
    # Test free slot finding
    print("📋 Step 3: Testing free slot detection...")
    try:
        free_slots = calendar_service.find_free_slots(start_date, end_date, duration_minutes=60)
        print(f"✅ Found {len(free_slots)} available slots")
        
        if free_slots:
            print("📅 Sample available slots:")
            for i, slot in enumerate(free_slots[:3]):
                start_time = datetime.fromisoformat(slot['start'])
                print(f"   {i+1}. {start_time.strftime('%Y-%m-%d %H:%M')} - {slot['duration_minutes']} minutes")
    except Exception as e:
        print(f"❌ Free slot detection failed: {e}")
        return False
    
    print("🎉 All tests passed! Calendar integration is working!")
    return True

if __name__ == "__main__":
    print("💡 First, install requirements if you haven't:")
    print("   pip install -r requirements.txt")
    print()
    print("💡 Make sure you have credentials.json in the root directory")
    print()
    
    test_calendar_integration()