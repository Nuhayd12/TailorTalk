import sys
import os

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

def test_agent_setup():
    """Test the conversation agent setup"""
    print("🤖 Testing TailorTalk Conversation Agent Setup...")
    
    try:
        # Test imports with direct import
        import importlib.util
        
        # Load the lg_agent module directly
        agent_path = os.path.join(backend_path, "agents", "lg_agent.py")
        
        if not os.path.exists(agent_path):
            print(f"❌ Agent file not found at: {agent_path}")
            print("📋 Make sure lg_agent.py exists in backend/agents/")
            return False
        
        spec = importlib.util.spec_from_file_location("lg_agent", agent_path)
        lg_agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lg_agent_module)
        
        TailorTalkAgent = lg_agent_module.TailorTalkAgent
        AgentState = lg_agent_module.AgentState
        
        print("✅ Agent imports successful!")
        
        # Check if OpenAI key is available
        from dotenv import load_dotenv
        load_dotenv()
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key or openai_key == "your_openai_key_here":
            print("⚠️  OpenAI API key not found in .env file")
            print("📋 To test the full agent:")
            print("   1. Get API key from: https://platform.openai.com/api-keys")
            print("   2. Add to .env: OPENAI_API_KEY=your-key-here")
            print("✅ Agent structure is ready!")
            return True
        
        # Test agent initialization
        print("🔄 Initializing agent...")
        agent = TailorTalkAgent(openai_key)
        print("✅ Agent initialized successfully!")
        
        # Test a simple conversation flow
        print("\n🗣️  Testing conversation flow...")
        response = agent.process_message("Hi, I want to schedule a meeting")
        
        if response and response.get("conversation_history"):
            print("✅ Conversation flow working!")
            last_message = response["conversation_history"][-1]["content"]
            print(f"🤖 Agent response: {last_message[:100]}...")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Check if all required packages are installed:")
        print("   pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        print(f"💡 Error details: {str(e)}")
        return False

if __name__ == "__main__":
    test_agent_setup()