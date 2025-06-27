import streamlit as st
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List

# Page configuration
st.set_page_config(
    page_title="TailorTalk - AI Calendar Assistant",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "https://tailortalk-production.up.railway.app"

# Custom CSS for better message display
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E86C1;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.8rem;
        border: 1px solid #ddd;
    }
    .user-message {
        background-color: #E3F2FD;
        margin-left: 2rem;
        color: #1565C0;
    }
    .assistant-message {
        background-color: #F8F9FA;
        margin-right: 2rem;
        color: #212529;
        border-left: 4px solid #2E86C1;
    }
    .message-content {
        color: #212529 !important;
        font-size: 1rem;
        line-height: 1.5;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "available_slots" not in st.session_state:
    st.session_state.available_slots = []
if "current_step" not in st.session_state:
    st.session_state.current_step = "greeting"
if "timezone" not in st.session_state:
    st.session_state.timezone = "GMT"
if "waiting_for_calendar" not in st.session_state:
    st.session_state.waiting_for_calendar = False
if "last_calendar_check" not in st.session_state:
    st.session_state.last_calendar_check = None

def check_calendar_status():
    """Check calendar connection status from the backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/calendar/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"calendar_connected": False, "status": "error"}
    except:
        return {"calendar_connected": False, "status": "error"}

# Auto-refresh mechanism for calendar connection
if st.session_state.waiting_for_calendar:
    # Check calendar status
    calendar_status = check_calendar_status()
    if calendar_status.get("calendar_connected"):
        # Calendar is now connected!
        st.session_state.waiting_for_calendar = False
        st.success("🎉 Calendar connected successfully! Refreshing page...")
        st.balloons()
        # Force page refresh
        st.rerun()
    else:
        # Still waiting, show auto-refresh with longer timeout and prominent manual link
        st.warning("⏳ Waiting for calendar connection...")
        st.info("🔗 **If the popup didn't open automatically, use the manual link below:**")
        
        # Prominent manual authorization link
        st.markdown("""
        <div style="text-align: center; background: #fff3cd; padding: 20px; border-radius: 10px; border: 2px solid #ffc107; margin: 10px 0;">
            <h3 style="color: #856404; margin: 0;">Manual Authorization</h3>
            <p style="color: #856404; margin: 10px 0;">Click the link below if the popup window didn't open:</p>
            <a href="https://tailortalk-production.up.railway.app/auth/calendar" target="_blank" 
               style="background: #007bff; color: white; padding: 15px 30px; text-decoration: none; 
                      border-radius: 5px; font-size: 16px; font-weight: bold; display: inline-block;">
               🔗 Authorize Google Calendar
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        # JavaScript countdown and auto-refresh
        st.markdown("""
        <div id="countdown" style="text-align: center; color: #666; margin: 10px 0; font-size: 14px;">
            Page will refresh automatically in <span id="timer">8</span> seconds...
        </div>
        <script>
        let countdown = 8;
        const timer = document.getElementById('timer');
        
        const interval = setInterval(function() {
            countdown--;
            if (timer) timer.textContent = countdown;
            
            if (countdown <= 0) {
                clearInterval(interval);
                window.location.reload();
            }
        }, 1000);
        </script>
        """, unsafe_allow_html=True)

def display_calendar_link(message_content):
    """Extract and display calendar links from assistant messages"""
    import re
    
    # Look for Google Calendar URLs in the message
    if "calendar.google.com" in message_content:
        # Extract all calendar URLs
        url_pattern = r'https://calendar\.google\.com[^\s\)\]\n]*'
        urls = re.findall(url_pattern, message_content)
        
        if urls:
            st.markdown("### 📅 Quick Access to Your Calendar")
            for url in urls:
                # Clean up the URL (remove any trailing punctuation)
                clean_url = url.rstrip('.,!?;)')
                st.markdown(f"🔗 **[📅 Open Google Calendar]({clean_url})**")
                st.info("👆 Click above to view your calendar and verify your events!")
                
                # Add some helpful buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📅 Day View", key=f"day_{hash(clean_url)}"):
                        day_url = clean_url.replace('/week/', '/day/').replace('/month/', '/day/').replace('/agenda', '/day')
                        st.markdown(f"[📅 Day View]({day_url})")
                
                with col2:
                    if st.button("📅 Week View", key=f"week_{hash(clean_url)}"):
                        week_url = clean_url.replace('/day/', '/week/').replace('/month/', '/week/').replace('/agenda', '/week')
                        st.markdown(f"[📅 Week View]({week_url})")
                
                with col3:
                    if st.button("📅 Month View", key=f"month_{hash(clean_url)}"):
                        month_url = clean_url.replace('/day/', '/month/').replace('/week/', '/month/').replace('/agenda', '/month')
                        st.markdown(f"[📅 Month View]({month_url})")

def parse_and_display_structured_data(message_content):
    """Parse JSON responses from tools and display structured data"""
    import re
    
    # Try to extract JSON from the message
    json_pattern = r'\{[^}]*"calendar_url"[^}]*\}'
    json_matches = re.findall(json_pattern, message_content)
    
    for json_str in json_matches:
        try:
            import json
            data = json.loads(json_str)
            
            if "calendar_url" in data:
                st.markdown("### 📅 Your Google Calendar")
                calendar_url = data["calendar_url"]
                st.markdown(f"🔗 **[Open Calendar - {data.get('view', 'Default')} View]({calendar_url})**")
                
                if data.get("current_date"):
                    st.info(f"📅 Current Date: {data['current_date']}")
                    
        except json.JSONDecodeError:
            continue

def send_message(message: str, timezone: str = None) -> Dict:
    """Send message to the API with timezone support"""
    try:
        # Use provided timezone or session state timezone
        tz = timezone or st.session_state.timezone
        
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "message": message,
                "session_id": st.session_state.session_id,
                "timezone": tz
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("🚫 Cannot connect to TailorTalk API. Make sure the backend is running on port 8000.")
        st.info("💡 Run: `python backend/api/app.py` in another terminal")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None
    
def display_calendar_events(events_data):
    """Display calendar events if returned from the agent"""
    if not events_data or not isinstance(events_data, dict):
        return
        
    events = events_data.get('events', [])
    if events:
        st.markdown("### 📅 Your Calendar Events")
        
        for i, event in enumerate(events):
            with st.expander(f"📋 {event.get('title', 'Event')} - {event.get('start_time', 'Unknown time')}"):
                st.write(f"**📅 Date:** {event.get('date', 'Unknown date')}")
                st.write(f"**⏰ Time:** {event.get('start_time', 'Unknown time')}")
                
                if event.get('description'):
                    st.write(f"**📝 Description:** {event.get('description')}")
                
                if event.get('location'):
                    st.write(f"**📍 Location:** {event.get('location')}")
                
                if event.get('calendar_link'):
                    st.markdown(f"🔗 [View in Google Calendar]({event.get('calendar_link')})")

def display_conversation():
    """Display the conversation history with proper styling and link detection"""
    if not st.session_state.conversation_history:
        return
        
    for i, message in enumerate(st.session_state.conversation_history):
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 You:</strong><br>
                <div class="message-content">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 TailorTalk:</strong><br>
                <div class="message-content">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Check for special content in the latest assistant message
            if i == len(st.session_state.conversation_history) - 1:
                # Check for authorization links first
                if "tailortalk-production.up.railway.app/auth/calendar" in message["content"]:
                    display_auth_link(message["content"])
                else:
                    # Check for other calendar links
                    display_calendar_link(message["content"])
                    parse_and_display_structured_data(message["content"])

def display_available_slots():
    """Display available time slots with timezone info"""
    if st.session_state.available_slots and len(st.session_state.available_slots) > 0:
        st.subheader(f"📅 Available Time Slots ({st.session_state.timezone})")
        
        for i, slot in enumerate(st.session_state.available_slots):
            try:
                start_time = datetime.fromisoformat(slot['start'])
                # Convert to display timezone if available
                if 'display_full' in slot:
                    time_display = slot['display_full']
                else:
                    time_display = f"{start_time.strftime('%A, %B %d at %I:%M %p')} ({st.session_state.timezone})"
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{i+1}.** {time_display}")               
                with col2:
                    st.write(f"{slot.get('duration_minutes', 60)} min")
                
                with col3:
                    if st.button(f"Select", key=f"slot_{i}"):
                        # Send slot selection
                        result = send_message(f"I want slot {i+1}")
                        if result:
                            st.session_state.session_id = result["session_id"]
                            st.session_state.conversation_history = result["conversation_history"]
                            st.session_state.current_step = result["current_step"]
                            st.session_state.available_slots = result.get("available_slots", [])
                            st.rerun()
            except Exception as e:
                st.error(f"Error displaying slot {i+1}: {e}")

def show_booking_status():
    """Show booking status based on current step"""
    if st.session_state.current_step == "slot_selection":
        st.info("📋 Waiting for confirmation to book your selected time slot...")
    elif st.session_state.current_step == "booking_creation":
        st.success("🎉 Booking your meeting...")
    elif st.session_state.current_step == "completion":
        st.info("💬 Ready to help with another booking or answer questions!")
    elif st.session_state.current_step == "ended":
        st.success("✅ Conversation completed!")
        if st.button("🔄 Start New Conversation", key="restart_after_end"):
            st.session_state.session_id = None
            st.session_state.conversation_history = []
            st.session_state.available_slots = []
            st.session_state.current_step = "greeting"
            st.rerun()
    elif (st.session_state.conversation_history and 
          "successfully booked" in st.session_state.conversation_history[-1].get("content", "").lower()):
        st.success("✅ Meeting successfully booked!")

# Main App Layout
st.markdown('<h1 class="main-header">🤖 TailorTalk</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #566573;">Your AI-Powered Calendar Assistant</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🔧 Controls")
    
    # API Status Check
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            st.success("✅ API Connected")
            
            # Show current backend timezone
            backend_tz = health_data.get("current_timezone", "GMT")
            st.info(f"🕐 Backend Timezone: {backend_tz}")
            
            # Check calendar status separately for more accurate results
            calendar_status = check_calendar_status()
            if calendar_status.get("calendar_connected"):
                st.success("✅ Calendar Connected")
                st.info("🎉 Ready to schedule meetings!")
            else:
                st.warning("⚠️ Calendar Not Connected")
                st.info("👆 Connect your calendar below to start scheduling")
            
            if health_data.get("openai_configured", False):
                st.success("✅ OpenAI Configured")
            else:
                st.warning("⚠️ OpenAI Not Configured")
        else:
            st.error("❌ API Not Responding")
    except:
        st.error("❌ API Offline")
        st.info("💡 Start the backend with:\n`python backend/api/app.py`")
    
    # Calendar Connection Button
    st.markdown("---")
    
    # Check if calendar is already connected
    calendar_status = check_calendar_status()
    
    if calendar_status.get("calendar_connected"):
        st.success("✅ Calendar Connected!")
        if st.button("🔄 Reconnect Calendar", key="sidebar_calendar_reconnect", use_container_width=True):
            st.markdown("""
            <script>
            window.open('https://tailortalk-production.up.railway.app/auth/calendar', '_blank', 'width=600,height=700,scrollbars=yes,resizable=yes');
            </script>
            """, unsafe_allow_html=True)
            st.info("📱 Opening authorization window...")
    else:
        if st.button("🔗 Connect Google Calendar", key="sidebar_calendar_connect", use_container_width=True):
            # Set waiting flag
            st.session_state.waiting_for_calendar = True
            st.markdown("""
            <script>
            window.open('https://tailortalk-production.up.railway.app/auth/calendar', '_blank', 'width=600,height=700,scrollbars=yes,resizable=yes');
            </script>
            """, unsafe_allow_html=True)
            st.info("📱 Opening authorization window...")
            st.info("⏳ If popup didn't open, you'll see a manual link after refresh!")
            # Trigger immediate rerun to start the auto-refresh loop
            st.rerun()
    
    st.divider()
    
    # Manual refresh for calendar status
    if st.session_state.waiting_for_calendar:
        st.markdown("### ⏳ Waiting for Calendar Connection")
        st.info("Authorization window opened. After connecting, click refresh below:")
        if st.button("🔄 Check Calendar Status", key="refresh_calendar", use_container_width=True):
            calendar_status = check_calendar_status()
            if calendar_status.get("calendar_connected"):
                st.session_state.waiting_for_calendar = False
                st.success("🎉 Calendar connected!")
                st.rerun()
            else:
                st.warning("⏳ Still waiting for connection...")
    
    # Timezone Selection
    st.header("🌍 Timezone")
    timezone_options = ["GMT", "IST", "AST", "EST", "PST"]
    selected_timezone = st.selectbox(
        "Select your timezone:",
        timezone_options,
        index=timezone_options.index(st.session_state.timezone)
    )
    
    if selected_timezone != st.session_state.timezone:
        st.session_state.timezone = selected_timezone
        st.success(f"✅ Timezone changed to {selected_timezone}")
        
        # Send timezone change message to backend
        if st.session_state.session_id:
            result = send_message(f"Change timezone to {selected_timezone}", selected_timezone)
            if result:
                st.session_state.conversation_history = result["conversation_history"]
                st.rerun()
    
    st.divider()
    
    # Session Management
    if st.button("🔄 New Conversation"):
        st.session_state.session_id = None
        st.session_state.conversation_history = []
        st.session_state.available_slots = []
        st.session_state.current_step = "greeting"
        st.rerun()
    
    if st.session_state.session_id:
        st.info(f"Session: {st.session_state.session_id[:8]}...")
        st.info(f"Step: {st.session_state.current_step}")
        st.info(f"Timezone: {st.session_state.timezone}")
    
    st.divider()
    
    # Quick Actions
    st.header("⚡ Quick Actions")
    
    quick_messages = [
        "I want to schedule a meeting",
        "Show me available times tomorrow", 
        # "Book a 30-minute call next week",
        # "Show me my calendar for today",
        "Can you open my calendar?",
        # "Check if my meeting was booked",
        # "What's on my schedule tomorrow?",
        "I need to schedule an interview",
        "What time is it now?"
    ]
    
    for quick_msg in quick_messages:
        if st.button(quick_msg, key=f"quick_{quick_msg}"):
            result = send_message(quick_msg)
            if result:
                st.session_state.session_id = result["session_id"]
                st.session_state.conversation_history = result["conversation_history"]
                st.session_state.current_step = result["current_step"]
                st.session_state.available_slots = result.get("available_slots", [])
                st.rerun()

# Main Chat Interface
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Chat with TailorTalk")
    
    # Display conversation
    if st.session_state.conversation_history:
        display_conversation()
    else:
        st.info("👋 Hi! I'm TailorTalk, your AI calendar assistant. How can I help you schedule your next meeting?")
    
    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type your message...", placeholder="I want to schedule a meeting")
        col_send, col_clear = st.columns([1, 1])
        
        with col_send:
            send_button = st.form_submit_button("Send 📤", use_container_width=True)
        
        with col_clear:
            if st.form_submit_button("Clear Chat 🗑️", use_container_width=True):
                st.session_state.conversation_history = []
                st.session_state.session_id = None
                st.session_state.available_slots = []
                st.session_state.current_step = "greeting"
                st.rerun()
    
    if send_button and user_input:
        with st.spinner("TailorTalk is thinking..."):
            result = send_message(user_input)
            if result:
                st.session_state.session_id = result["session_id"]
                st.session_state.conversation_history = result["conversation_history"]
                st.session_state.current_step = result["current_step"]
                st.session_state.available_slots = result.get("available_slots", [])
                st.rerun()

with col2:
    st.header("📊 Session Info")
    
    if st.session_state.session_id:
        st.info(f"**Session ID:** {st.session_state.session_id[:12]}...")
        st.info(f"**Messages:** {len(st.session_state.conversation_history)}")
        st.info(f"**Current Step:** {st.session_state.current_step}")
        st.info(f"**Your Timezone:** {st.session_state.timezone}")
    
    # Show booking status
    show_booking_status()
    
    # Display available slots
    display_available_slots()

# Footer
st.markdown("---")
st.markdown("🚀 **TailorTalk** - Built with FastAPI, Streamlit, LangGraph & GPT-4")

def display_auth_link(message_content):
    """Extract and display authorization links prominently"""
    import re
    
    # Look for Railway auth URLs
    auth_pattern = r'https://tailortalk-production\.up\.railway\.app/auth/calendar'
    if re.search(auth_pattern, message_content):
        st.markdown("### 🔐 Calendar Authorization Required")
        st.markdown("**Click the button below to connect your Google Calendar:**")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔗 **Connect Google Calendar**", key="auth_button", use_container_width=True):
                # Set waiting flag
                st.session_state.waiting_for_calendar = True
                st.markdown("""
                <script>
                window.open('https://tailortalk-production.up.railway.app/auth/calendar', '_blank', 'width=600,height=700,scrollbars=yes,resizable=yes');
                </script>
                """, unsafe_allow_html=True)
                st.success("📱 Opening authorization window...")
                st.info("⏳ If popup didn't open, you'll see a manual link after refresh!")
                st.balloons()
                # Trigger immediate rerun to start the auto-refresh loop
                st.rerun()
        
        st.info("� You can also use the sidebar button to connect your calendar!")
        
        # Add helpful instructions
        with st.expander("📋 Step-by-step instructions"):
            st.markdown("""
            1. **Click** the "Connect Google Calendar" button above
            2. **Sign in** to your Google account if prompted  
            3. **Allow** TailorTalk to access your calendar
            4. **Wait** for the page to refresh automatically
            5. **Send your message** again - it will work!
            """)