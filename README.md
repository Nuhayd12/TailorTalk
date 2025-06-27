🤖 TailorTalk - AI-Powered Calendar Assistant

An intelligent, LLM-powered calendar booking assistant that understands natural language and automates meeting scheduling with Google Calendar integration.

📋 Table of Contents
🎯 Project Overview
🏗️ Architecture
✨ Key Features
🔧 Technical Stack
📁 Project Structure
🚀 Installation & Setup
🎮 Usage Guide
🧪 Testing
🛡️ Edge Cases Handled
🔮 Future Scope
⚠️ Security Notice
🎯 Project Overview

TailorTalk is an advanced AI calendar assistant that revolutionizes meeting scheduling through:

Natural Language Understanding: Processes complex scheduling requests in conversational format
Smart Calendar Integration: Seamlessly connects with Google Calendar API
Multi-Timezone Support: Handles GMT, IST, AST, EST, PST with automatic conversions
Intelligent Slot Finding: Automatically detects available time slots
Real-time Booking: Creates calendar events instantly with proper notifications

🏗️ Architecture

Component Breakdown:

1. Frontend (Streamlit): Interactive web interface with real-time chat
2. Backend (FastAPI): REST API handling requests and session management
3. Smart Agent: GPT-4 powered conversational AI with function calling
4. Calendar Service: Google Calendar API integration with OAuth2
5. Tools System: Modular functions for specific tasks (scheduling, viewing, etc.)

✨ Key Features

Core Functionality

✅ Natural Language Scheduling: "Book a meeting tomorrow at 3 PM"
✅ Multi-Timezone Support: Automatic timezone detection and conversion
✅ Smart Date Parsing: Understands "29th June", "next Friday", "tomorrow"
✅ Real-time Availability: Checks actual Google Calendar for free slots
✅ Instant Booking: Creates calendar events with descriptions and notifications
✅ Calendar Viewing: Display existing events with proper timezone formatting
🎯 Advanced Features
✅ Conversational Flow: Maintains context throughout the conversation
✅ Error Handling: Graceful fallbacks for API failures or invalid inputs
✅ Session Management: Persistent conversations across multiple interactions
✅ Timezone Intelligence: Shows times like "4:00 PM (IST)" for clarity
✅ Calendar Links: Direct links to Google Calendar for verification
🛠️ Technical Excellence
✅ LangChain Integration: Function calling with structured tools
✅ OAuth2 Authentication: Secure Google Calendar access
✅ REST API Design: Clean, documented endpoints
✅ Real-time Updates: Live conversation updates in UI
✅ Cross-platform Compatibility: Works on Windows, macOS, Linux

🔧 Technical Stack
Component	Technology	Purpose
Frontend	Streamlit	Interactive web interface
Backend	FastAPI	REST API & session management
AI Engine	OpenAI GPT-4	Natural language processing
LLM Framework	LangChain	Tool calling & agent orchestration
Calendar API	Google Calendar	Event management
Authentication	OAuth2	Secure calendar access
Timezone	pytz	Multi-timezone support
HTTP Client	requests	API communication


📁 Project Structure
🚀 Installation & Setup

- Prerequisites

- Python 3.8 or higher
- Google Cloud Console account
- OpenAI API account

Step 1: Clone Repository
Step 2: Install Dependencies

Required packages:

Step 3: Google Calendar API Setup

1. Go to Google Cloud Console
2. Create a new project or select existing one
3. Enable Google Calendar API:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google Calendar API"
   - Click "Enable"
4. Create OAuth 2.0 Credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Set application type to "Desktop Application"
   - Download the JSON file

5. Rename the downloaded file to credentials.json
6. Place it in /api directory

Step 4: Environment Configuration

Edit .env:

# Google Calendar API
GOOGLE_CREDENTIALS_FILE=credentials.json

# API Configuration
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000

# Calendar Settings
DEFAULT_MEETING_DURATION=60
BUSINESS_START_HOUR=9
BUSINESS_END_HOUR=17
DEFAULT_TIMEZONE=GMT

# OpenAI API Key (REQUIRED)
OPENAI_API_KEY="your-openai-api-key-here"
<!-- ANTHROPIC_API_KEY=your_anthropic_key_here  # Optional -->

🎮 Usage Guide

Option 1: Run Full Application

<!-- Start Backend Server: -->
Server starts on http://localhost:8000

<!-- Start Frontend (New Terminal): -->
UI opens at http://localhost:8501

Option 2: Testing Mode

<!-- Test Calendar Integration: -->
This validates Google Calendar connectivity

Option 3: API Testing

Check API Health:

<!-- curl http://localhost:8000/health -->

Test Chat Endpoint: 

<!-- curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Schedule a meeting tomorrow at 3 PM", "timezone": "IST"}' -->

🎯 How to Use TailorTalk

Basic Scheduling:

1. Open the Streamlit app at http://localhost:8501
2. Select your timezone from the sidebar (GMT, IST, AST, etc.)
3. Type natural language requests:
   - "Schedule a meeting tomorrow at 3 PM"
   - "Book a 1-hour call on 29th June"
   - "Find available slots next Friday"

<!-- Quick Actions Available: -->

🗓️ "I want to schedule a meeting"
⏰ "Show me available times tomorrow"
📅 "Can you open my calendar?"
🎯 "I need to schedule an interview"
🕐 "What time is it now?"

Advanced Features:

1. View Calendar: "Show me my schedule for today"
2. Timezone Changes: "Change timezone to IST"
3. Specific Dates: "29th June 3-4 PM IST 1 hour meeting"
4. Calendar Links: Get direct Google Calendar URLs

🧪 Testing

<!-- Manual Testing Checklist: -->

✅ Calendar Integration
✅ Backend API

<!-- Start backend: python backend/api/app.py -->

<!-- Check health: http://localhost:8000/health -->

<!-- Test chat: Use curl or Postman -->

✅ Frontend UI

Start Streamlit: streamlit run frontend/streamlit_app.py

1. Test timezone selection
2. Test quick actions
3. Test natural language input

✅ End-to-End Workflow

1. Say: "Schedule a meeting tomorrow at 3 PM"
2. Select a time slot from results
3. Confirm booking
4. Verify in Google Calendar

<!-- 🛡️ Edge Cases Handled -->
🔧 Date & Time Parsing

✅ Ambiguous Dates: "29th June" → Detects current/next year
✅ Invalid Dates: "February 30th" → Graceful fallback
✅ Past Dates: Automatically suggests future alternatives
✅ Timezone Conflicts: Converts between GMT/IST/AST correctly
✅ Business Hours: Only shows slots within 9 AM - 5 PM

🔧 Calendar Integration
✅ API Failures: Graceful error handling with user feedback
✅ Authentication Expiry: Automatic token refresh
✅ Rate Limiting: Implements proper retry mechanisms
✅ Empty Calendar: Handles no events gracefully
✅ Conflicting Events: Detects overlaps and suggests alternatives

🔧 User Experience
✅ Session Management: Maintains context across conversations
✅ Connection Errors: Clear error messages with solutions
✅ Invalid Input: Helpful suggestions for corrections
✅ Multiple Requests: Handles rapid-fire questions
✅ Browser Refresh: Preserves session state
🔧 Technical Robustness

✅ API Timeouts: 30-second timeout with retry logic
✅ Memory Management: Efficient session storage
✅ Cross-platform: Works on Windows/macOS/Linux
✅ Environment Variables: Secure credential management
✅ Error Logging: Comprehensive debugging information

🔮 Future Scope
<!-- 🚀 Phase 1: Enhanced User Experience -->


📅 Advanced Calendar Features
✨ Multi-Calendar Support: Handle personal, work, and shared calendars
✨ Recurring Meetings: "Schedule weekly standup every Monday"
✨ Meeting Templates: Pre-defined meeting types with durations
✨ Conflict Resolution: Smart suggestions when time slots overlap
✨ Calendar Sync: Two-way sync with Outlook, Apple Calendar
🎯 Smarter Scheduling
✨ Meeting Preferences: Learn user's preferred meeting times
✨ Buffer Time: Automatic 15-minute buffers between meetings
✨ Meeting Duration Detection: "Quick chat" = 15 mins, "Deep dive" = 2 hours
✨ Location Integration: Suggest meeting rooms or video links
✨ Attendee Management: Add multiple participants with email invites


<!-- 🚀 Phase 2: AI-Powered Intelligence -->


🧠 Advanced NLP Features
✨ Intent Recognition: Detect cancellations, rescheduling, updates
✨ Context Awareness: "Move our 3 PM meeting to tomorrow"
✨ Email Integration: Process meeting requests from emails
✨ Voice Commands: "Hey TailorTalk, schedule my doctor appointment"
✨ Multi-language Support: Spanish, French, German, Hindi
📊 Analytics & Insights
✨ Meeting Analytics: Track meeting frequency, duration, patterns
✨ Productivity Insights: Suggest optimal meeting-free focus time
✨ Calendar Health Score: Analyze meeting density and suggest improvements
✨ Team Coordination: Find common free time for team meetings
✨ Meeting Cost Calculator: Show time investment for recurring meetings


<!-- 🚀 Phase 3: Enterprise Features -->


🏢 Business Integration
✨ CRM Integration: Sync with Salesforce, HubSpot for client meetings
✨ Project Management: Connect with Jira, Trello for project meetings
✨ HR Systems: Interview scheduling with ATS integration
✨ Conference Room Booking: Reserve physical spaces automatically
✨ Travel Integration: Account for travel time between locations
🔐 Enterprise Security
✨ SSO Integration: Active Directory, OKTA authentication
✨ Role-based Access: Admin controls for organization settings
✨ Audit Logs: Complete trail of all scheduling activities
✨ Data Encryption: End-to-end encryption for sensitive meetings
✨ Compliance: GDPR, HIPAA compliance for regulated industries


<!-- 🚀 Phase 4: Communication & Collaboration -->


💬 Currently Commented Features (Ready for Implementation)
✨ "Book a 30-minute call next week": Duration-specific scheduling
✨ "Show me my calendar for today": Enhanced daily agenda view
✨ "Check if my meeting was booked": Real-time booking verification
✨ "What's on my schedule tomorrow?": Proactive schedule briefings
🌐 Communication Channels
✨ Slack Integration: Schedule meetings directly from Slack
✨ Microsoft Teams: Native Teams meeting creation
✨ WhatsApp Bot: Schedule via WhatsApp messages
✨ Email Assistant: Parse and respond to meeting invites
✨ Mobile App: Native iOS/Android applications


<!-- 🚀 Phase 5: AI Automation -->


🤖 Intelligent Automation
✨ Auto-scheduling: AI suggests and books optimal meeting times
✨ Smart Rescheduling: Automatically handle cancellations and conflicts
✨ Meeting Preparation: Auto-generate agendas based on context
✨ Follow-up Automation: Schedule follow-up meetings automatically
✨ Travel Optimization: Minimize travel time between meetings
🔮 Predictive Features
✨ Meeting Success Prediction: Analyze likelihood of productive meetings
✨ Optimal Time Suggestions: Machine learning for best meeting times
✨ Burnout Prevention: Detect over-scheduling and suggest breaks
✨ Seasonal Patterns: Adapt to holiday seasons and vacation patterns
✨ Performance Correlation: Link meeting patterns to productivity metrics
🎯 Unique Innovation Opportunities
🌟 Cutting-edge Features
✨ AR/VR Integration: Schedule meetings in virtual spaces
✨ AI Meeting Notes: Auto-transcription and action item extraction
✨ Emotion Detection: Gauge meeting satisfaction and engagement
✨ Carbon Footprint: Track and reduce travel-related emissions
✨ Wellness Integration: Consider circadian rhythms for meeting scheduling
🔗 Platform Ecosystem
✨ API Marketplace: Third-party integrations and plugins
✨ White-label Solution: Customizable for enterprise clients
✨ Industry-specific Modules: Healthcare, Legal, Education variants
✨ Global Expansion: Multi-timezone optimization for international teams
✨ Accessibility Features: Support for users with disabilities


<!-- ⚠️ Security Notice -->
🔐 Credentials & Privacy
Important: For security and privacy reasons, the following sensitive files are NOT included in this repository:

<!-- 🚫 Excluded Files: -->
1. credentials.json - Google OAuth2 credentials
2. token.pickle - Stored authentication tokens
3. .env file with real API keys

<!-- ✅ Required Setup: -->

Create your own credentials.json:

1. Follow Google Cloud Console setup steps above
2. Download your own OAuth2 credentials
3. Place in credentials.json

<!-- Configure your .env file: -->

1. Copy the example .env structure provided
2. Insert your own OpenAI API key
3. Ensure all paths and settings match your environment

<!-- Authentication Flow: -->

1. First run will trigger OAuth2 flow
2. Authenticate via browser when prompted
3. token.pickle will be created automatically

<!-- 🤝 Contributing -->

This project demonstrates advanced AI integration with calendar systems. The modular architecture allows for easy extension and customization for specific business needs.

<!-- Key Technical Achievements: -->

✅ Natural language to structured API calls
✅ Multi-timezone complexity handling
✅ Real-time calendar integration
✅ Conversational AI with memory
✅ Production-ready error handling

<!-- 📞 Support -->
For implementation support, feature requests, or enterprise integration opportunities, the codebase is thoroughly documented and ready for production deployment.

<!-- Architecture Benefits: -->

🔧 Modular Design: Easy to extend and customize
🚀 Scalable Backend: FastAPI with async support
🧠 AI-First Approach: LangChain tools for extensibility
🔒 Security Ready: OAuth2 and environment-based configuration
📊 Production Ready: Comprehensive error handling and logging

<!-- Built with ❤️ using Python, FastAPI, Streamlit, LangChain & GPT-4 -->