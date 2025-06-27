import sys
import os

def test_agent_structure():
    """Test if agent files exist and basic structure is correct"""
    print("🔍 Testing TailorTalk Agent Structure...")
    
    # Check if required files exist
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    agent_path = os.path.join(backend_path, 'agents', 'lg_agent.py')
    calendar_path = os.path.join(backend_path, 'cal_service', 'google_calendar.py')
    models_path = os.path.join(backend_path, 'models', 'calendar_model.py')
    
    # Check files
    files_to_check = [
        (agent_path, "Agent file (lg_agent.py)"),
        (calendar_path, "Calendar service"),
        (models_path, "Calendar models"),
        (".env", "Environment file"),
        ("requirements.txt", "Requirements file")
    ]
    
    all_good = True
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {description} found")
        else:
            print(f"❌ {description} missing: {file_path}")
            all_good = False
    
    # Test imports one by one
    print("\n🔍 Testing individual imports...")
    
    # Add backend to path
    sys.path.insert(0, backend_path)
    
    try:
        import importlib.util
        
        # Test LangGraph import
        import langgraph
        print("✅ LangGraph imported successfully")
        
        # Test LangChain imports
        from langchain_core.messages import HumanMessage
        print("✅ LangChain core imported successfully")
        
        # Test OpenAI import
        from langchain_openai import ChatOpenAI
        print("✅ LangChain OpenAI imported successfully")
        
        # Test calendar service import
        spec = importlib.util.spec_from_file_location(
            "google_calendar", 
            calendar_path
        )
        if spec:
            google_calendar_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(google_calendar_module)
            print("✅ Google Calendar service imported successfully")
        
        print("\n🎉 All basic imports working!")
        
        if all_good:
            print("✅ Agent structure is ready!")
            print("📋 Next steps:")
            print("   1. Run: pip install -r requirements.txt")
            print("   2. Get OpenAI API key and add to .env")
            print("   3. Test with: python agent_test_setup.py")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_agent_structure()