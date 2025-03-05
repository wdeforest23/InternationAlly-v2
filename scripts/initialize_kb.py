import os
import sys
from app.utils.rag_system import RAGSystem
import shutil

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def initialize_knowledge_base(urls_file: str):
    # Clear existing index and documents
    if os.path.exists("faiss_index"):
        os.remove("faiss_index")
    if os.path.exists("docs_store.pkl"):
        os.remove("docs_store.pkl")
    
    # Initialize RAG system
    rag = RAGSystem()
    
    # Load URLs from working_urls.txt
    with open(urls_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"Found {len(urls)} URLs to process")
    
    # Add documents to vector database
    rag.add_documents_from_urls(urls)
    
    print(f"Successfully processed {len(urls)} URLs")
    
    # Test the system with a sample query
    test_query = "What are the requirements for maintaining F-1 student status?"
    print("\nTesting the system with a sample query:")
    print(f"Query: {test_query}")
    
    results = rag.query(test_query, n_results=2)
    print("\nRetrieved relevant documents:")
    for i, result in enumerate(results, 1):
        print(f"\nDocument {i} (Similarity: {result['similarity']:.2f}):")
        print(f"Source: {result['metadata']['url']}")
        print(f"Content preview: {result['content'][:200]}...")
    
    response = rag.generate_response(test_query, results)
    print("\nGenerated Response:")
    print(response)

if __name__ == "__main__":
    # Create documents directory if it doesn't exist
    if not os.path.exists('documents'):
        os.makedirs('documents')
    
    initialize_knowledge_base("documents/working_urls.txt") 