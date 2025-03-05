import os
from dotenv import load_dotenv
import vertexai
from vertexai.preview.generative_models import GenerativeModel, ChatSession
from vertexai.generative_models import SafetySetting, HarmCategory, HarmBlockThreshold
from openai import OpenAI
from app.utils.rag_system import RAGSystem

def test_gemini_connection():
    """Test connection to Google's Gemini model"""
    try:
        print("\n=== Testing Gemini Connection ===")
        
        # Configure safety settings
        safety_config = [
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.OFF,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=HarmBlockThreshold.OFF,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=HarmBlockThreshold.OFF,
            ),
        ]
        
        vertexai.init(project="internationally", location="us-central1")
        model = GenerativeModel("gemini-2.0-flash-001", safety_settings=safety_config)
        chat = model.start_chat(response_validation=False)
        
        # Test with a simple query
        response = chat.send_message("What is the capital of France?", stream=True)
        text_response = []
        for chunk in response:
            if hasattr(chunk, 'text'):
                text_response.append(chunk.text)
        print("✓ Gemini response:", "".join(text_response))
        return True
        
    except Exception as e:
        print(f"❌ Gemini test failed: {str(e)}")
        return False

def test_openai_connection():
    """Test connection to OpenAI's GPT-4"""
    try:
        print("\n=== Testing OpenAI Connection ===")
        client = OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"}
            ],
            temperature=0.7,
        )
        print("✓ GPT-4 response:", response.choices[0].message.content)
        return True
        
    except Exception as e:
        print(f"❌ OpenAI test failed: {str(e)}")
        return False

def test_rag_system():
    """Test RAG system functionality"""
    try:
        print("\n=== Testing RAG System ===")
        rag = RAGSystem()
        
        # Test query about F-1 status
        query = "What are the requirements for maintaining F-1 status?"
        docs = rag.query(query, n_results=2)
        
        print("✓ Retrieved relevant documents:")
        for i, doc in enumerate(docs, 1):
            print(f"\nDocument {i} (Similarity: {doc['similarity']:.2f}):")
            print(f"Source: {doc['metadata']['url']}")
            print(f"Preview: {doc['content'][:150]}...")
        
        response = rag.generate_response(query, docs)
        print("\n✓ Generated RAG response:", response[:200], "...")
        return True
        
    except Exception as e:
        print(f"❌ RAG system test failed: {str(e)}")
        return False

if __name__ == "__main__":
    load_dotenv()
    
    print("Testing AI Connections...")
    gemini_success = test_gemini_connection()
    openai_success = test_openai_connection()
    rag_success = test_rag_system()
    
    print("\n=== Test Summary ===")
    print(f"Gemini Connection: {'✓' if gemini_success else '❌'}")
    print(f"OpenAI Connection: {'✓' if openai_success else '❌'}")
    print(f"RAG System: {'✓' if rag_success else '❌'}") 