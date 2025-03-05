import asyncio
from app.utils.chat_manager import ChatManager
import json
import logging
import os
from datetime import datetime

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def check_rag_files():
    """Check if RAG system files exist and show their details"""
    print("\n=== Checking RAG System Files ===")
    
    files_to_check = [
        "data/faiss_index",
        "data/docs_store.pkl"
    ]
    
    all_files_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
            print(f"\n{file_path}:")
            print(f"- Last modified: {mod_time}")
            print(f"- Size: {size:.2f} MB")
        else:
            print(f"\n❌ {file_path} not found!")
            all_files_exist = False
    
    return all_files_exist

async def test_rag_functionality():
    """Test RAG system functionality"""
    # First check if files exist
    files_exist = await check_rag_files()
    if not files_exist:
        print("\n⚠️ RAG system files not found in correct location.")
        print("Please run initialize_rag.py first to create the index and document store.")
        return
    
    chat_manager = ChatManager()
    print("\n=== Testing RAG Query ===")
    
    test_query = "What are the requirements for maintaining F-1 status?"
    print(f"\nQuery: {test_query}")
    
    try:
        # Test direct RAG query
        rag_docs = chat_manager.rag.query(test_query, n_results=3)
        print("\nRAG Documents Retrieved:")
        if rag_docs:
            for i, doc in enumerate(rag_docs, 1):
                print(f"\nDocument {i}:")
                print(f"Similarity Score: {doc.get('similarity', 'N/A')}")
                print(f"Source URL: {doc.get('metadata', {}).get('url', 'N/A')}")
                print(f"Content Preview: {doc.get('content', '')[:200]}...")
                
            # Test response generation
            rag_response = chat_manager.rag.generate_response(test_query, rag_docs)
            print("\nGenerated Response:")
            print(rag_response[:500])
        else:
            print("No documents retrieved from RAG system")
    except Exception as e:
        print(f"Error testing RAG: {str(e)}")

async def test_chat():
    chat_manager = ChatManager()
    
    # Test only student info queries
    queries = [
        {
            "description": "F-1 Status Query",
            "query": "What are the requirements for maintaining F-1 status?"
        },
        {
            "description": "OPT Documentation Query",
            "query": "What documents do I need for OPT application?"
        }
    ]
    
    for test_case in queries:
        print(f"\n=== Testing: {test_case['description']} ===")
        print(f"Query: {test_case['query']}")
        
        try:
            # First analyze the query
            analysis = await chat_manager.analyze_query(test_case['query'])
            print("\nIntent Analysis:")
            print(json.dumps(analysis, indent=2))
            
            # Then process the full message
            response = await chat_manager.process_message(test_case['query'])
            
            if response['success']:
                print("\nRAG System Results:")
                if response['api_data']['rag']:
                    rag_docs = response['api_data']['rag']
                    for i, doc in enumerate(rag_docs, 1):
                        print(f"\nDocument {i}:")
                        print(f"Source: {doc.get('metadata', {}).get('url', 'N/A')}")
                        print(f"Content Preview: {doc.get('content', '')[:200]}...")
                else:
                    print("No RAG data retrieved")
                
                print("\nFinal Response:")
                print(response['response'][:500])
            else:
                print(f"Error: {response.get('error')}")
            
        except Exception as e:
            print(f"Error processing query: {str(e)}")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    print("Testing RAG System Integration")
    asyncio.run(test_rag_functionality())
    print("\nTesting Chat Processing")
    asyncio.run(test_chat()) 