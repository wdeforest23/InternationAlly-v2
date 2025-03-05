from app.utils.rag_system import RAGSystem

def initialize_knowledge_base(urls_file: str):
    # Initialize RAG system
    rag = RAGSystem()
    
    # Load URLs
    urls = rag.load_urls_from_file(urls_file)
    
    # Add documents to vector database
    rag.add_documents_from_urls(urls)
    
    print(f"Successfully processed {len(urls)} URLs")

if __name__ == "__main__":
    initialize_knowledge_base("documents/urls.txt") 