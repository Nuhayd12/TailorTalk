## TailorTalk - AI-Powered Calendar Assistant 🤖

TailorTalk is an intelligent, LLM-powered calendar booking assistant that understands natural language and automates meeting scheduling with seamless Google Calendar integration. It revolutionizes how you manage your schedule by providing a conversational interface for all your meeting needs.

-----

## 📋 Table of Contents

* [🎯 Project Overview](#-project-overview)
* [🏗️ Architecture](#️-architecture)
* [✨ Key Features](#-key-features)
* [🔧 Technical Stack](#-technical-stack)
* [📁 Project Structure](#-project-structure)
* [🚀 Installation & Setup](#-installation--setup)
* [🎮 Usage Guide](#-usage-guide)
* [🧪 Testing](#-testing)
* [🛡️ Edge Cases Handled](#-edge-cases-handled)
* [🔮 Future Scope](#-future-scope)
* [⚠️ Security Notice](#️-security-notice)
* [🤝 Contributing](#-contributing)
* [📞 Support](#-support)

-----

## 🎯 Project Overview

TailorTalk streamlines meeting scheduling by offering:

  * **Natural Language Understanding:** Processes complex scheduling requests in a conversational format.
  * **Smart Calendar Integration:** Seamlessly connects with the Google Calendar API.
  * **Multi-Timezone Support:** Handles GMT, IST, AST, EST, PST with automatic conversions.
  * **Intelligent Slot Finding:** Automatically detects available time slots.
  * **Real-time Booking:** Creates calendar events instantly with proper notifications.

-----

## 🏗️ Architecture

TailorTalk employs a modular and scalable architecture:

**Component Breakdown:**

1.  **Frontend (Streamlit):** Provides an interactive web interface with real-time chat capabilities.
2.  **Backend (FastAPI):** Serves as the REST API, handling requests and managing session states.
3.  **Smart Agent:** A GPT-4 powered conversational AI that leverages function calling to understand and execute user commands.
4.  **Calendar Service:** Manages Google Calendar API integration, including secure OAuth2 authentication.
5.  **Tools System:** A collection of modular functions for specific tasks like scheduling, viewing, and modifying calendar events.

-----

## ✨ Key Features

### Core Functionality

  * ✅ **Natural Language Scheduling:** Easily schedule meetings with phrases like "Book a meeting tomorrow at 3 PM."
  * ✅ **Multi-Timezone Support:** Automatic timezone detection and conversion for seamless global coordination.
  * ✅ **Smart Date Parsing:** Understands various date formats such as "29th June," "next Friday," or "tomorrow."
  * ✅ **Real-time Availability:** Checks your actual Google Calendar for free slots before booking.
  * ✅ **Instant Booking:** Creates calendar events with descriptions and notifications instantly.
  * ✅ **Calendar Viewing:** Displays existing events with proper timezone formatting for clarity.

### Advanced Features

  * ✅ **Conversational Flow:** Maintains context throughout the conversation for a natural user experience.
  * ✅ **Error Handling:** Provides graceful fallbacks for API failures or invalid inputs.
  * ✅ **Session Management:** Ensures persistent conversations across multiple interactions.
  * ✅ **Timezone Intelligence:** Shows times clearly, e.g., "4:00 PM (IST)."
  * ✅ **Calendar Links:** Provides direct links to Google Calendar for easy verification of booked events.

### Technical Excellence

  * ✅ **LangChain Integration:** Utilizes LangChain for robust function calling with structured tools.
  * ✅ **OAuth2 Authentication:** Ensures secure access to Google Calendar.
  * ✅ **REST API Design:** Features clean, well-documented endpoints for easy integration.
  * ✅ **Real-time Updates:** Provides live conversation updates in the UI.
  * ✅ **Cross-platform Compatibility:** Works seamlessly on Windows, macOS, and Linux.

-----

## 🔧 Technical Stack

| Component     | Technology      | Purpose                               |
| :------------ | :-------------- | :------------------------------------ |
| Frontend      | Streamlit       | Interactive web interface             |
| Backend       | FastAPI         | REST API & session management         |
| AI Engine     | OpenAI GPT-4    | Natural language processing           |
| LLM Framework | LangChain       | Tool calling & agent orchestration    |
| Calendar API  | Google Calendar | Event management                      |
| Authentication| OAuth2          | Secure calendar access                |
| Timezone      | `pytz`          | Multi-timezone support                |
| HTTP Client   | `requests`      | API communication                     |

-----

## 📁 Project Structure

```
├── backend/
│   ├── api/
│   │   ├── app.py                  # FastAPI application entry point
│   │   ├── auth.py                 # OAuth2 authentication logic
│   │   ├── calendar_service.py     # Google Calendar API interactions
│   │   ├── config.py               # Application configuration
│   │   ├── models.py               # Pydantic models for request/response
│   │   └── utils.py                # Utility functions
│   ├── agent/
│   │   ├── agent.py                # LangChain agent definition
│   │   ├── tools.py                # Custom tools for the agent
│   │   └── prompts.py              # LLM prompts
│   └── main.py                     # Backend server runner
├── frontend/
│   ├── streamlit_app.py            # Streamlit frontend application
│   └── utils.py                    # Frontend utility functions
├── .env.example                    # Example environment variables file
├── requirements.txt                # Python dependencies
├── README.md                       # Project README
└── run.sh                          # (Optional) Script to run both backend and frontend
```

-----

## 🚀 Installation & Setup

### Prerequisites

  * Python 3.8 or higher
  * Google Cloud Console account
  * OpenAI API account

### Step 1: Clone Repository

```bash
git clone <repository_url>
cd TailorTalk
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Google Calendar API Setup

1.  Go to [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project or select an existing one.
3.  **Enable Google Calendar API:**
      * Navigate to "APIs & Services" → "Library."
      * Search for "Google Calendar API."
      * Click "Enable."
4.  **Create OAuth 2.0 Credentials:**
      * Go to "APIs & Services" → "Credentials."
      * Click "Create Credentials" → "OAuth 2.0 Client IDs."
      * Set the application type to "Desktop Application."
      * Download the JSON file.
5.  Rename the downloaded file to `credentials.json`.
6.  Place `credentials.json` in the `/backend/api` directory.

### Step 4: Environment Configuration

Create a `.env` file in the root directory of the project and populate it as follows:

```ini
# Google Calendar API
GOOGLE_CREDENTIALS_FILE=backend/api/credentials.json

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
# ANTHROPIC_API_KEY=your_anthropic_key_here  # Optional, if using Anthropic models
```

-----

## 🎮 Usage Guide

### Option 1: Run Full Application

**Start Backend Server:**

```bash
unicorn app:app --reload
```

The server will start on `http://localhost:8000`.

**Start Frontend (New Terminal):**

```bash
streamlit run frontend/streamlit_app.py
```

The UI will open in your browser at `http://localhost:8501`.

### Option 2: Testing Mode

**Test Calendar Integration:**

```bash
python backend/api/calendar_service.py
```

This validates Google Calendar connectivity and authentication.

### Option 3: API Testing

**Check API Health:**

```bash
curl http://localhost:8000/health
```

**Test Chat Endpoint:**

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Schedule a meeting tomorrow at 3 PM", "timezone": "IST"}'
```

### 🎯 How to Use TailorTalk

**Basic Scheduling:**

1.  Open the Streamlit app at `http://localhost:8501`.
2.  Select your timezone from the sidebar (GMT, IST, AST, etc.).
3.  Type natural language requests in the chat interface:
      * "Schedule a meeting tomorrow at 3 PM"
      * "Book a 1-hour call on 29th June"
      * "Find available slots next Friday"

**Quick Actions Available:**

You can also use the predefined quick action buttons:

  * 🗓️ "I want to schedule a meeting"
  * ⏰ "Show me available times tomorrow"
  * 📅 "Can you open my calendar?"
  * 🎯 "I need to schedule an interview"
  * 🕐 "What time is it now?"

**Advanced Features:**

  * **View Calendar:** "Show me my schedule for today."
  * **Timezone Changes:** "Change timezone to IST."
  * **Specific Dates:** "29th June 3-4 PM IST 1 hour meeting."
  * **Calendar Links:** Get direct Google Calendar URLs for booked events.

-----

## 🧪 Testing

### Manual Testing Checklist:

✅ **Calendar Integration**

1.  Start backend: `python backend/api/app.py`
2.  Check health: `http://localhost:8000/health`
3.  Test chat: Use `curl` or Postman to send requests to `/chat` endpoint.

✅ **Frontend UI**

1.  Start Streamlit: `streamlit run frontend/streamlit_app.py`
2.  Test timezone selection in the sidebar.
3.  Test quick action buttons.
4.  Test natural language input in the chat.

✅ **End-to-End Workflow**

1.  In the Streamlit app, say: "Schedule a meeting tomorrow at 3 PM."
2.  Select a time slot from the results provided by TailorTalk.
3.  Confirm the booking.
4.  Verify the newly created event directly in your Google Calendar.

-----

## 🛡️ Edge Cases Handled

### 🔧 Date & Time Parsing

  * ✅ **Ambiguous Dates:** "29th June" → Automatically detects current/next year based on context.
  * ✅ **Invalid Dates:** "February 30th" → Provides graceful fallbacks and helpful error messages.
  * ✅ **Past Dates:** Automatically suggests future alternatives when a past date is provided.
  * ✅ **Timezone Conflicts:** Correctly converts and manages times between GMT, IST, AST, etc.
  * ✅ **Business Hours:** Only suggests and books slots within defined business hours (9 AM - 5 PM by default).

### 🔧 Calendar Integration

  * ✅ **API Failures:** Implements graceful error handling with informative user feedback.
  * ✅ **Authentication Expiry:** Automatic token refresh ensures continuous access.
  * ✅ **Rate Limiting:** Implements proper retry mechanisms to handle API rate limits.
  * ✅ **Empty Calendar:** Handles scenarios where no events exist in the user's calendar gracefully.
  * ✅ **Conflicting Events:** Detects overlaps with existing events and suggests alternative available times.

### 🔧 User Experience

  * ✅ **Session Management:** Maintains conversational context across multiple interactions.
  * ✅ **Connection Errors:** Displays clear error messages with suggested solutions for network issues.
  * ✅ **Invalid Input:** Provides helpful suggestions for correcting misinterpreted or invalid inputs.
  * ✅ **Multiple Requests:** Efficiently handles rapid-fire questions and commands.
  * ✅ **Browser Refresh:** Preserves the session state even if the browser is refreshed.

### 🔧 Technical Robustness

  * ✅ **API Timeouts:** Configured with a 30-second timeout and retry logic for API calls.
  * ✅ **Memory Management:** Employs efficient session storage to optimize resource usage.
  * ✅ **Cross-platform:** Verified to work on Windows, macOS, and Linux operating systems.
  * ✅ **Environment Variables:** Securely manages sensitive credentials through environment variables.
  * ✅ **Error Logging:** Provides comprehensive debugging information for troubleshooting.

-----

## 🔮 Future Scope

### 🚀 Phase 1: Enhanced User Experience

#### 📅 Advanced Calendar Features

  * **Multi-Calendar Support:** Handle personal, work, and shared calendars.
  * **Recurring Meetings:** "Schedule weekly standup every Monday."
  * **Meeting Templates:** Pre-defined meeting types with customizable durations.
  * **Conflict Resolution:** Smart suggestions and automatic adjustments when time slots overlap.
  * **Calendar Sync:** Two-way synchronization with Outlook and Apple Calendar.

#### 🎯 Smarter Scheduling

  * **Meeting Preferences:** Learn and adapt to a user's preferred meeting times and days.
  * **Buffer Time:** Automatically add 15-minute buffers between meetings.
  * **Meeting Duration Detection:** Intelligently infer duration from phrases like "quick chat" (15 mins) or "deep dive" (2 hours).
  * **Location Integration:** Suggest meeting rooms or integrate with video conferencing links.
  * **Attendee Management:** Add multiple participants and send email invitations directly.

-----

### 🚀 Phase 2: AI-Powered Intelligence

#### 🧠 Advanced NLP Features

  * **Intent Recognition:** Detect cancellations, rescheduling requests, and meeting updates.
  * **Context Awareness:** Understand commands like "Move our 3 PM meeting to tomorrow."
  * **Email Integration:** Process meeting requests and confirmations from emails.
  * **Voice Commands:** Enable hands-free scheduling: "Hey TailorTalk, schedule my doctor appointment."
  * **Multi-language Support:** Expand language support to Spanish, French, German, Hindi, etc.

#### 📊 Analytics & Insights

  * **Meeting Analytics:** Track meeting frequency, duration, and patterns over time.
  * **Productivity Insights:** Suggest optimal meeting-free focus times.
  * **Calendar Health Score:** Analyze meeting density and suggest improvements for a balanced schedule.
  * **Team Coordination:** Find common free time slots for team meetings more efficiently.
  * **Meeting Cost Calculator:** Show the time investment for recurring meetings and team time.

-----

### 🚀 Phase 3: Enterprise Features

#### 🏢 Business Integration

  * **CRM Integration:** Sync meeting details with Salesforce, HubSpot for client interactions.
  * **Project Management:** Connect with Jira, Trello for project-related meeting scheduling.
  * **HR Systems:** Streamline interview scheduling with Applicant Tracking Systems (ATS).
  * **Conference Room Booking:** Automatically reserve physical meeting spaces.
  * **Travel Integration:** Account for travel time between different locations for in-person meetings.

#### 🔐 Enterprise Security

  * **SSO Integration:** Support for Single Sign-On with Active Directory, OKTA authentication.
  * **Role-based Access:** Implement administrative controls for organization-wide settings.
  * **Audit Logs:** Maintain a complete trail of all scheduling activities for compliance.
  * **Data Encryption:** Ensure end-to-end encryption for sensitive meeting information.
  * **Compliance:** Adhere to regulatory standards like GDPR and HIPAA for regulated industries.

-----

### 🚀 Phase 4: Communication & Collaboration

#### 💬 Currently Commented Features (Ready for Implementation)

  * "Book a 30-minute call next week": Enables duration-specific scheduling.
  * "Show me my calendar for today": Provides an enhanced daily agenda view.
  * "Check if my meeting was booked": Offers real-time booking verification.
  * "What's on my schedule tomorrow?": Provides proactive schedule briefings.

#### 🌐 Communication Channels

  * **Slack Integration:** Schedule meetings directly from Slack channels.
  * **Microsoft Teams:** Native integration for creating Teams meetings.
  * **WhatsApp Bot:** Schedule meetings via WhatsApp messages.
  * **Email Assistant:** Parse and respond to meeting invitations received via email.
  * **Mobile App:** Develop native iOS/Android applications for on-the-go scheduling.

-----

### 🚀 Phase 5: AI Automation

#### 🤖 Intelligent Automation

  * **Auto-scheduling:** AI suggests and books optimal meeting times based on availability and preferences.
  * **Smart Rescheduling:** Automatically handles cancellations and conflicts, suggesting new times.
  * **Meeting Preparation:** Auto-generate agendas based on meeting context and participants.
  * **Follow-up Automation:** Automatically schedule follow-up meetings or tasks.
  * **Travel Optimization:** Minimize travel time by suggesting meeting locations or times.

#### 🔮 Predictive Features

  * **Meeting Success Prediction:** Analyze factors to predict the likelihood of productive meetings.
  * **Optimal Time Suggestions:** Use machine learning to suggest the best times for specific meeting types.
  * **Burnout Prevention:** Detect over-scheduling and suggest breaks or rescheduling.
  * **Seasonal Patterns:** Adapt scheduling suggestions to holiday seasons and vacation patterns.
  * **Performance Correlation:** Link meeting patterns to individual or team productivity metrics.

#### 🎯 Unique Innovation Opportunities

#### 🌟 Cutting-edge Features

  * **AR/VR Integration:** Schedule and participate in meetings in virtual reality spaces.
  * **AI Meeting Notes:** Auto-transcription and extraction of action items from meetings.
  * **Emotion Detection:** Gauge meeting satisfaction and engagement levels during calls.
  * **Carbon Footprint:** Track and help reduce travel-related emissions from business meetings.
  * **Wellness Integration:** Consider circadian rhythms and personal wellness for meeting scheduling.

#### 🔗 Platform Ecosystem

  * **API Marketplace:** Allow third-party integrations and plugins to extend functionality.
  * **White-label Solution:** Offer a customizable version for enterprise clients.
  * **Industry-specific Modules:** Develop variants tailored for Healthcare, Legal, and Education sectors.
  * **Global Expansion:** Further optimize multi-timezone support for international teams.
  * **Accessibility Features:** Ensure support for users with disabilities, adhering to accessibility standards.

-----

## ⚠️ Security Notice

### 🔐 Credentials & Privacy

**Important:** For security and privacy reasons, the following sensitive files are **NOT** included in this repository:

1.  `credentials.json` - Your Google OAuth2 credentials.
2.  `token.pickle` - Stored authentication tokens generated during the OAuth flow.
3.  `.env` file with real API keys (only `.env.example` is provided).

**✅ Required Setup:**

1.  **Create your own `credentials.json`:**

      * Follow the [Google Cloud Console setup steps](https://www.google.com/search?q=%23step-3-google-calendar-api-setup) above.
      * Download your own OAuth2 credentials.
      * Place it in the `backend/api/` directory.

2.  **Configure your `.env` file:**

      * Copy the example `.env.example` structure.
      * Insert your own OpenAI API key.
      * Ensure all paths and settings match your environment.

**Authentication Flow:**

The first time you run the application, it will trigger the OAuth2 flow. You will be prompted to authenticate via your browser. Upon successful authentication, a `token.pickle` file will be created automatically to store your credentials securely for future use.

-----

## 🤝 Contributing

This project demonstrates advanced AI integration with calendar systems. Its modular architecture is designed for easy extension and customization to meet specific business needs.

**Key Technical Achievements:**

  * ✅ Natural language to structured API calls conversion.
  * ✅ Robust handling of multi-timezone complexity.
  * ✅ Real-time integration with Google Calendar.
  * ✅ Conversational AI with memory and context retention.
  * ✅ Production-ready error handling and graceful fallbacks.

-----

## 📞 Support

For implementation support, feature requests, or enterprise integration opportunities, the codebase is thoroughly documented and designed for production deployment.

**Architecture Benefits:**

  * 🔧 **Modular Design:** Easy to extend and customize for diverse requirements.
  * 🚀 **Scalable Backend:** Built with FastAPI, leveraging its async capabilities for high performance.
  * 🧠 **AI-First Approach:** Utilizes LangChain tools for enhanced extensibility and AI capabilities.
  * 🔒 **Security Ready:** Implements OAuth2 and environment-based configuration for secure operations.
  * 📊 **Production Ready:** Features comprehensive error handling and logging for reliable deployment.

-----

Built with ❤️ using Python, FastAPI, Streamlit, LangChain & GPT-4.
