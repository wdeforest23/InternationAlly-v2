from rag_system import RAGSystem
import json

def test_rag_system():
    # Initialize RAG system
    rag = RAGSystem()
    
    # Test queries
    test_queries = [
        "What exactly constitutes a full-time course load? How many classes or units are required?",
        "What are the three types of Reduced Course Load (RCL) and their requirements?",
        "What are the specific requirements for maintaining F-1 status regarding course load?",
        "Can you explain the rules about working on campus, including how many hours are allowed?",
        "What is the process for applying for OPT, and when should I start?"
    ]
    
    print("Testing RAG System with specific queries...\n")
    
    for query in test_queries:
        print(f"Query: {query}")
        print("-" * 80)
        
        # Get relevant documents
        docs = rag.query(query, n_results=3)
        
        print("Top relevant sources:")
        for i, doc in enumerate(docs, 1):
            similarity = doc['similarity']
            url = doc['metadata']['url']
            content_preview = doc['content'][:150].replace('\n', ' ')
            print(f"\n{i}. Similarity: {similarity:.2f}")
            print(f"   URL: {url}")
            print(f"   Preview: {content_preview}...")
        
        # Generate response
        response = rag.generate_response(query, docs)
        
        print("\nGenerated Response:")
        print(response)
        print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    test_rag_system() 