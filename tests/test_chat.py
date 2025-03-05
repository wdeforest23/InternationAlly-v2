import pytest
import asyncio
import os
from ..utils.chat_manager import ChatManager, ChatError

@pytest.fixture
async def chat_manager():
    manager = ChatManager()
    yield manager
    manager.clear_history()

@pytest.mark.asyncio
async def test_basic_query(chat_manager, monkeypatch):
    # Mock the Vertex AI response
    def mock_predict(*args, **kwargs):
        class MockResponse:
            text = '{"intents": ["general_information"], "parameters": {}}'
        return MockResponse()
    
    monkeypatch.setattr(chat_manager.model, "predict", mock_predict)
    
    response = await chat_manager.process_message(
        "What are the requirements for maintaining F-1 status?"
    )
    assert response["success"]
    assert "full-time" in response["response"].lower()
    assert "course load" in response["response"].lower()

@pytest.mark.asyncio
async def test_housing_query(chat_manager):
    response = await chat_manager.process_message(
        "I'm looking for a 2-bedroom apartment near UChicago under $2000"
    )
    assert response["success"]
    assert "housing" in response["analysis"]["intents"]
    assert "price" in response["analysis"]["parameters"]

@pytest.mark.asyncio
async def test_location_query(chat_manager):
    response = await chat_manager.process_message(
        "What restaurants are near campus?"
    )
    assert response["success"]
    assert "location_info" in response["analysis"]["intents"]
    assert "Hyde Park" in response["response"]

@pytest.mark.asyncio
async def test_error_handling(chat_manager):
    # Test with invalid API key
    chat_manager.openai_client.api_key = "invalid_key"
    response = await chat_manager.process_message("Hello")
    assert not response["success"]
    assert "error" in response

@pytest.mark.asyncio
async def test_conversation_history(chat_manager):
    await chat_manager.process_message("Hello")
    await chat_manager.process_message("How are you?")
    assert len(chat_manager.conversation_history) == 4  # 2 messages + 2 responses

def test_chat_manager_initialization():
    """Test that ChatManager properly raises errors when API keys are missing"""
    # Save original keys
    original_openai_key = os.getenv('OPENAI_API_KEY')
    original_google_key = os.getenv('GOOGLE_API_KEY')
    
    try:
        # Test missing OpenAI key
        os.environ['OPENAI_API_KEY'] = ''
        with pytest.raises(ChatError, match="OpenAI API key not found"):
            ChatManager()
        
        # Test missing Google key
        os.environ['OPENAI_API_KEY'] = 'dummy_key'
        os.environ['GOOGLE_API_KEY'] = ''
        with pytest.raises(ChatError, match="Google API key not found"):
            ChatManager()
            
    finally:
        # Restore original keys
        if original_openai_key:
            os.environ['OPENAI_API_KEY'] = original_openai_key
        if original_google_key:
            os.environ['GOOGLE_API_KEY'] = original_google_key 