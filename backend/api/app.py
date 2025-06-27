from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from datetime import datetime
from dotenv import load_dotenv
import uuid
import sys

# Add parent directories to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(backend_dir)

# Add paths for imports
sys.path.insert(0, root_dir)
sys.path.insert(0, backend_dir)
sys.path.insert(0, current_dir)

# Load environment variables
load_dotenv()

# Import our modules with proper path handling
try:
    from agents.smart_agent import SmartTailorTalkAgent
except ImportError:
    try:
        from backend.agents.smart_agent import SmartTailorTalkAgent
    except ImportError:
        # Fallback for Railway deployment
        agent_path = os.path.join(backend_dir, 'agents', 'smart_agent.py')
        import importlib.util
        spec = importlib.util.spec_from_file_location("smart_agent", agent_path)
        smart_agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(smart_agent_module)
        SmartTailorTalkAgent = smart_agent_module.SmartTailorTalkAgent

# Updated Pydantic models for API
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    timezone: Optional[str] = "GMT"  # Added timezone field

class ChatResponse(BaseModel):
    response: str
    session_id: str
    conversation_history: List[Dict[str, str]]
    current_step: str
    available_slots: Optional[List[Dict[str, Any]]] = None

# Initialize FastAPI app
app = FastAPI(
    title="TailorTalk Smart Calendar Agent API",
    description="LLM-powered intelligent calendar booking assistant",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Local development
        "https://*.streamlit.app",  # Streamlit Cloud
        "https://tailortalkagenticai.streamlit.app"  # Your specific app
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize smart agent
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY:
    OPENAI_KEY = OPENAI_KEY.strip().strip('"').strip("'")

if not OPENAI_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

print(f"🔑 OpenAI Key detected: {OPENAI_KEY[:7]}...")

try:
    print("🧠 Initializing Smart TailorTalk Agent...")
    agent = SmartTailorTalkAgent(OPENAI_KEY, timezone="GMT")
    print("✅ Smart TailorTalk Agent initialized successfully!")
except Exception as e:
    print(f"❌ Failed to initialize smart agent: {e}")
    agent = None

# Session storage
sessions: Dict[str, Dict] = {}

@app.get("/")
async def root():
    return {"message": "TailorTalk Smart Calendar Agent API", "status": "active", "version": "2.0.0"}

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Process any message through the intelligent LLM agent"""
    try:
        session_id = message.session_id or str(uuid.uuid4())
        
        if agent is None:
            return ChatResponse(
                response="I'm currently setting up my AI brain. Please make sure your OpenAI API key is configured.",
                session_id=session_id,
                conversation_history=[
                    {"role": "user", "content": message.message},
                    {"role": "assistant", "content": "Please configure OpenAI API key to enable full functionality."}
                ],
                current_step="configuration_needed",
                available_slots=[]
            )
        
        # Check if calendar is connected
        calendar_connected = False
        if agent and agent.calendar_service:
            try:
                calendar_connected = (
                    agent.calendar_service.service is not None or
                    agent.calendar_service.credentials is not None
                )
            except:
                calendar_connected = False
        
        if not calendar_connected:
            return ChatResponse(
                response="🔐 **Please connect your Google Calendar first to use TailorTalk!**\n\nClick this link to authorize your calendar:\n\nhttps://tailortalk-production.up.railway.app/auth/calendar\n\n📋 **Steps:**\n1. Click the link above\n2. Sign in to your Google account\n3. Allow TailorTalk to access your calendar\n4. Return here and start chatting!\n\nAfter connecting, you'll be able to schedule meetings, check availability, and manage your calendar through our AI assistant.",
                session_id=session_id,
                conversation_history=[
                    {"role": "user", "content": message.message},
                    {"role": "assistant", "content": "🔐 Please connect your Google Calendar first! Click: https://tailortalk-production.up.railway.app/auth/calendar"}
                ],
                current_step="calendar_connection_required",
                available_slots=[]
            )
        
        # Set timezone if provided and different from current
        if message.timezone and message.timezone != agent.timezone:
            agent.set_timezone(message.timezone)
            print(f"🕐 Agent timezone updated to: {message.timezone}")
        
        # Get current state
        current_state = sessions.get(session_id)
        
        # Process message through smart agent
        result = agent.process_message(message.message, current_state)
        
        # Update session
        sessions[session_id] = result
        
        # Get latest response
        latest_message = ""
        if result.get("conversation_history"):
            for msg in reversed(result["conversation_history"]):
                if msg["role"] == "assistant":
                    latest_message = msg["content"]
                    break
        
        return ChatResponse(
            response=latest_message,
            session_id=session_id,
            conversation_history=result.get("conversation_history", []),
            current_step="smart_conversation",  # No more rigid steps!
            available_slots=result.get("available_slots", [])
        )
        
    except Exception as e:
        print(f"❌ Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear a conversation session"""
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/health")
async def health_check():
    """Health check"""
    try:
        openai_configured = (
            OPENAI_KEY and 
            OPENAI_KEY.strip() and 
            OPENAI_KEY != "your_openai_key_here" and
            OPENAI_KEY.startswith('sk-')
        )
        
        calendar_connected = False
        agent_ready = False
        
        if agent:
            agent_ready = True
            try:
                calendar_connected = agent.calendar_service.service is not None
            except:
                calendar_connected = False
        
        return {
            "status": "healthy",
            "agent_type": "smart_llm_agent",
            "calendar_connected": calendar_connected,
            "agent_ready": agent_ready,
            "active_sessions": len(sessions),
            "openai_configured": openai_configured,
            "current_timezone": agent.timezone if agent else "GMT",
            "version": "2.0.0"
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/auth/calendar")
async def start_calendar_auth():
    """Start Google Calendar OAuth flow"""
    try:
        if agent and agent.calendar_service:
            auth_url = agent.calendar_service.get_authorization_url()
            return {"auth_url": auth_url, "message": "Visit this URL to authorize calendar access"}
        else:
            raise HTTPException(status_code=500, detail="Calendar service not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/callback", response_class=HTMLResponse)
async def calendar_auth_callback(code: str):
    """Handle Google Calendar OAuth callback"""
    try:
        print(f"🔄 OAuth callback received with code: {code[:20]}...")
        
        if agent and agent.calendar_service:
            print("📋 Processing OAuth callback...")
            success = agent.calendar_service.handle_oauth_callback(code)
            print(f"🎯 OAuth callback result: {success}")
            
            if success:
                return HTMLResponse("""
                <html>
                    <head><title>Calendar Connected!</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px; background: #f0f2f6;">
                        <div style="background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto;">
                            <h1 style="color: #28a745;">✅ Calendar Successfully Connected!</h1>
                            <p style="font-size: 18px; color: #333;">Your Google Calendar is now connected to TailorTalk.</p>
                            <p style="color: #666;">You can close this window and return to the app to start scheduling!</p>
                            <div style="margin-top: 30px;">
                                <button onclick="window.close()" style="background: #007bff; color: white; border: none; padding: 12px 24px; border-radius: 5px; font-size: 16px; cursor: pointer;">Close Window</button>
                            </div>
                        </div>
                        <script>
                            setTimeout(() => {
                                window.close();
                            }, 5000);
                        </script>
                    </body>
                </html>
                """)
            else:
                print("❌ OAuth callback failed")
                raise HTTPException(status_code=400, detail="Failed to connect calendar")
        else:
            print("❌ Agent or calendar service not available")
            raise HTTPException(status_code=500, detail="Calendar service not initialized")
    except Exception as e:
        print(f"❌ OAuth callback error: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(f"""
        <html>
            <head><title>Connection Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px; background: #f0f2f6;">
                <div style="background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto;">
                    <h1 style="color: #dc3545;">❌ Connection Failed</h1>
                    <p style="color: #333;">Error: {str(e)}</p>
                    <p style="color: #666;">Please try again or contact support.</p>
                    <div style="margin-top: 30px;">
                        <button onclick="window.close()" style="background: #6c757d; color: white; border: none; padding: 12px 24px; border-radius: 5px; font-size: 16px; cursor: pointer;">Close Window</button>
                    </div>
                </div>
            </body>
        </html>
        """)
    except Exception as e:
        return HTMLResponse(f"""
        <html>
            <head><title>Connection Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px; background: #f0f2f6;">
                <div style="background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto;">
                    <h1 style="color: #dc3545;">❌ Connection Failed</h1>
                    <p style="color: #333;">Error: {str(e)}</p>
                    <p style="color: #666;">Please try again or contact support.</p>
                    <div style="margin-top: 30px;">
                        <button onclick="window.close()" style="background: #6c757d; color: white; border: none; padding: 12px 24px; border-radius: 5px; font-size: 16px; cursor: pointer;">Close Window</button>
                    </div>
                </div>
            </body>
        </html>
        """)

@app.get("/calendar/status")
async def calendar_status():
    """Check if calendar is connected"""
    try:
        calendar_connected = False
        auth_url = "https://tailortalk-production.up.railway.app/auth/calendar"
        debug_info = {}
        
        if agent and agent.calendar_service:
            try:
                # Check if calendar is connected
                has_credentials = agent.calendar_service.credentials is not None
                has_service = agent.calendar_service.service is not None
                
                debug_info = {
                    "has_credentials": has_credentials,
                    "has_service": has_service,
                    "credentials_expired": False
                }
                
                # Check if credentials are expired
                if has_credentials:
                    try:
                        debug_info["credentials_expired"] = agent.calendar_service.credentials.expired
                    except:
                        debug_info["credentials_expired"] = "unknown"
                
                calendar_connected = has_credentials and has_service
                
                # If connected, verify with a test call
                if calendar_connected:
                    try:
                        # Make a test API call to verify connection
                        calendar_list = agent.calendar_service.service.calendarList().list().execute()
                        debug_info["test_call_success"] = True
                        debug_info["calendar_count"] = len(calendar_list.get('items', []))
                        print(f"📊 Calendar status verified: {debug_info['calendar_count']} calendars found")
                    except Exception as test_error:
                        debug_info["test_call_success"] = False
                        debug_info["test_error"] = str(test_error)
                        print(f"⚠️ Calendar test call failed: {test_error}")
                        # Still consider connected if we have credentials and service
                        
                # If not connected, provide auth URL
                if not calendar_connected:
                    try:
                        auth_url = agent.calendar_service.get_authorization_url()
                    except Exception as auth_error:
                        print(f"⚠️ Could not generate auth URL: {auth_error}")
                        auth_url = "https://tailortalk-production.up.railway.app/auth/calendar"
            except Exception as check_error:
                print(f"⚠️ Error checking calendar status: {check_error}")
                calendar_connected = False
                debug_info["check_error"] = str(check_error)
        else:
            debug_info["agent_exists"] = agent is not None
            debug_info["calendar_service_exists"] = agent.calendar_service is not None if agent else False
        
        response = {
            "calendar_connected": calendar_connected,
            "auth_url": auth_url,
            "message": "Calendar connected! ✅" if calendar_connected else "Calendar not connected. Please authorize access.",
            "status": "connected" if calendar_connected else "disconnected"
        }
        
        # Add debug info in development
        if not os.getenv('RAILWAY_ENVIRONMENT'):
            response["debug"] = debug_info
            
        return response
        
    except Exception as e:
        print(f"❌ Error in calendar_status endpoint: {e}")
        return {
            "calendar_connected": False,
            "auth_url": "https://tailortalk-production.up.railway.app/auth/calendar",
            "message": f"Error checking calendar status: {str(e)}",
            "status": "error"
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)