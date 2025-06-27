from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
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
                response="🔐 Please connect your Google Calendar first to use TailorTalk! Click the link below to authorize:\n\n🔗 **Connect Calendar**: https://tailortalk-production.up.railway.app/auth/calendar\n\nAfter connecting, you'll be able to schedule meetings, check availability, and manage your calendar through our AI assistant.",
                session_id=session_id,
                conversation_history=[
                    {"role": "user", "content": message.message},
                    {"role": "assistant", "content": "Please connect your Google Calendar first to use TailorTalk! Visit the authorization link to get started."}
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

@app.get("/auth/callback")
async def calendar_auth_callback(code: str):
    """Handle Google Calendar OAuth callback"""
    try:
        if agent and agent.calendar_service:
            success = agent.calendar_service.handle_oauth_callback(code)
            if success:
                return {"message": "Calendar successfully connected!", "status": "success"}
            else:
                raise HTTPException(status_code=400, detail="Failed to connect calendar")
        else:
            raise HTTPException(status_code=500, detail="Calendar service not initialized")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calendar/status")
async def calendar_status():
    """Check if calendar is connected"""
    try:
        calendar_connected = False
        auth_url = "https://tailortalk-production.up.railway.app/auth/calendar"
        
        if agent and agent.calendar_service:
            try:
                # Check if calendar is connected
                calendar_connected = (
                    agent.calendar_service.service is not None or
                    agent.calendar_service.credentials is not None
                )
                
                # If not connected, provide auth URL
                if not calendar_connected:
                    try:
                        auth_url = agent.calendar_service.get_authorization_url()
                    except:
                        auth_url = "https://tailortalk-production.up.railway.app/auth/calendar"
            except:
                calendar_connected = False
        
        return {
            "calendar_connected": calendar_connected,
            "auth_url": auth_url,
            "message": "Calendar connected! ✅" if calendar_connected else "Calendar not connected. Please authorize access.",
            "status": "connected" if calendar_connected else "disconnected"
        }
        
    except Exception as e:
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