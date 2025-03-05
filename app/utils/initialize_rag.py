from app.utils.rag_system import RAGSystem
import os

def initialize_knowledge_base():
    """Initialize the RAG system with URLs from data/documents"""
    print("Initializing RAG system...")
    
    # Initialize RAG system
    rag = RAGSystem()
    
    # Load URLs from data/documents
    urls_file = os.path.join("data", "documents")
    if not os.path.exists(urls_file):
        raise FileNotFoundError(f"URLs file not found at: {urls_file}")
    
    with open(urls_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"Found {len(urls)} URLs to process")
    
    # Add documents to vector database
    rag.add_documents_from_urls(urls)
    
    print(f"Successfully processed {len(urls)} URLs")
    
    # Test the system
    test_query = "What are the requirements for maintaining F-1 status?"
    print("\nTesting RAG system with query:", test_query)
    
    docs = rag.query(test_query, n_results=2)
    if docs:
        print("\nRetrieved documents:")
        for i, doc in enumerate(docs, 1):
            print(f"\nDocument {i}:")
            print(f"Source: {doc['metadata']['url']}")
            print(f"Similarity: {doc['similarity']:.2f}")
            print(f"Preview: {doc['content'][:200]}...")

if __name__ == "__main__":
    initialize_knowledge_base() 