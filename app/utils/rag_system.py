import os
import json
import requests
import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
import faiss
import pickle
import google.generativeai as genai
from openai import OpenAI

class RAGSystem:
    def __init__(self, index_path: str = "data/faiss_index", docs_path: str = "data/docs_store.pkl"):
        # Initialize API clients
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        
        # Initialize or load FAISS index
        self.index_path = index_path
        self.docs_path = docs_path
        self.dimension = 1536  # OpenAI embedding dimension
        
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
            with open(docs_path, 'rb') as f:
                self.documents = pickle.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.documents = []

    def load_urls_from_file(self, file_path: str) -> List[str]:
        """Load URLs from a text file."""
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if line.strip()]

    def fetch_and_process_url(self, url: str) -> Dict[str, Any]:
        """Fetch content from URL and process it."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.select('nav, footer, .breadcrumb, #sidebar-first'):
                element.decompose()
            
            # Get main content
            main_content = soup.find('main') or soup.find(class_='main-content') or soup
            
            # Extract title
            title = main_content.find('h1').get_text(strip=True) if main_content.find('h1') else ''
            
            # Extract content with headers
            content_parts = []
            if title:
                content_parts.append(f"# {title}\n")
            
            for element in main_content.find_all(['h2', 'h3', 'h4', 'p', 'ul', 'ol']):
                if element.name.startswith('h'):
                    # Add appropriate markdown heading level
                    level = int(element.name[1])
                    content_parts.append(f"\n{'#' * level} {element.get_text(strip=True)}\n")
                elif element.name == 'p':
                    content_parts.append(element.get_text(strip=True))
                elif element.name in ['ul', 'ol']:
                    for li in element.find_all('li'):
                        content_parts.append(f"- {li.get_text(strip=True)}")
            
            # Join content with proper spacing
            text = '\n\n'.join(content_parts)
            
            return {
                'url': url,
                'title': title,
                'content': text,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error processing URL {url}: {str(e)}")
            return None

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks with improved sectioning."""
        # Split text into sections based on headers
        sections = []
        current_section = []
        
        for line in text.split('\n'):
            if line.strip().startswith('#'):  # Header found
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        # Process each section into chunks
        chunks = []
        for section in sections:
            words = section.split()
            if len(words) < chunk_size:
                chunks.append(section)
                continue
            
            for i in range(0, len(words), chunk_size - overlap):
                chunk = ' '.join(words[i:i + chunk_size])
                # Include the section header in each chunk if available
                header = section.split('\n')[0] if section.split('\n')[0].startswith('#') else ''
                if header and not chunk.startswith('#'):
                    chunk = f"{header}\n\n{chunk}"
                chunks.append(chunk)
        
        return chunks

    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding from OpenAI API."""
        response = self.openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return np.array(response.data[0].embedding, dtype=np.float32)

    def add_documents_from_urls(self, urls: List[str]) -> None:
        """Process URLs and add documents to FAISS index with improved chunking."""
        total_chunks = 0
        
        for url in urls:
            doc = self.fetch_and_process_url(url)
            if not doc:
                continue
            
            # Extract title from content if available
            title = doc['content'].split('\n')[0] if doc['content'].startswith('#') else ''
            
            chunks = self.chunk_text(doc['content'])
            print(f"Processing {url}: {len(chunks)} chunks created")
            
            for i, chunk in enumerate(chunks):
                # Get embedding for chunk
                embedding = self.get_embedding(chunk)
                
                # Add to FAISS index
                self.index.add(embedding.reshape(1, -1))
                
                # Store document info with more metadata
                self.documents.append({
                    'content': chunk,
                    'metadata': {
                        'url': url,
                        'chunk_id': i,
                        'title': title,
                        'timestamp': doc['timestamp']
                    }
                })
                total_chunks += 1
        
        # Save index and documents
        faiss.write_index(self.index, self.index_path)
        with open(self.docs_path, 'wb') as f:
            pickle.dump(self.documents, f)
        
        print(f"\nTotal chunks created: {total_chunks}")

    def query(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Query the vector database."""
        query_embedding = self.get_embedding(query_text)
        
        # Search FAISS index
        D, I = self.index.search(query_embedding.reshape(1, -1), n_results)
        
        results = []
        for i, (dist, idx) in enumerate(zip(D[0], I[0])):
            if idx < len(self.documents):  # Ensure valid index
                doc = self.documents[idx]
                results.append({
                    'content': doc['content'],
                    'metadata': doc['metadata'],  # We're now storing metadata as a nested dict
                    'similarity': 1 / (1 + dist)  # Convert distance to similarity score
                })
        
        return results

    def generate_response(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Generate response using GPT-4 with improved context handling."""
        # Prepare context with better formatting
        context_parts = []
        for doc in context_docs:
            source_url = doc['metadata']['url']
            content = doc['content']
            title = doc['metadata'].get('title', '')
            
            # Extract relevant section from URL for better context
            section = source_url.split('/')[-1].replace('-', ' ').title()
            context_parts.append(f"Source ({section}):\n{title}\n{content}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        system_message = """You are InternationAlly, an AI assistant helping international students.
        Use the following context to answer the user's question accurately and comprehensively.
        If the context contains the information, use it and cite specific details.
        If the context doesn't contain enough information, say so clearly and provide general guidance.
        Always be helpful, clear, and precise with requirements and numbers when available.
        
        Context:
        {context}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message.format(context=context)},
                    {"role": "user", "content": query}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error generating the response. Please try your question again."

# Helper functions for creating and managing knowledge bases

def create_knowledge_base_from_texts(texts: List[str], metadata_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create a knowledge base from a list of texts and metadata
    
    Args:
        texts: List of text documents
        metadata_list: List of metadata dictionaries for each document
    
    Returns:
        Knowledge base as a list of documents
    """
    if len(texts) != len(metadata_list):
        raise ValueError("Number of texts and metadata entries must match")
    
    knowledge_base = []
    for text, metadata in zip(texts, metadata_list):
        knowledge_base.append({
            "content": text,
            "metadata": metadata
        })
    
    return knowledge_base

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split a text into overlapping chunks
    
    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk
        overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Find the end of the chunk
        end = start + chunk_size
        
        # If we're not at the end of the text, try to find a good breaking point
        if end < len(text):
            # Try to find a period, question mark, or exclamation point followed by a space
            for i in range(end - 1, start + chunk_size // 2, -1):
                if i < len(text) and text[i] in ['.', '!', '?'] and i + 1 < len(text) and text[i + 1] == ' ':
                    end = i + 1
                    break
        
        # Add the chunk
        chunks.append(text[start:min(end, len(text))])
        
        # Move to the next chunk with overlap
        start = end - overlap
    
    return chunks

def create_knowledge_base_from_documents(documents: List[Dict[str, Any]], chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    """
    Create a knowledge base from a list of documents, chunking the content
    
    Args:
        documents: List of documents with 'content' and 'metadata' fields
        chunk_size: Maximum size of each chunk
        overlap: Overlap between chunks
    
    Returns:
        Knowledge base as a list of chunked documents
    """
    knowledge_base = []
    
    for doc in documents:
        content = doc['content']
        metadata = doc['metadata']
        
        # Chunk the content
        chunks = chunk_text(content, chunk_size, overlap)
        
        # Add each chunk as a separate document
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_index'] = i
            chunk_metadata['total_chunks'] = len(chunks)
            
            knowledge_base.append({
                "content": chunk,
                "metadata": chunk_metadata
            })
    
    return knowledge_base

# Example usage
if __name__ == "__main__":
    # Create a RAG system
    rag = RAGSystem()
    
    # Add some documents
    rag.add_document({
        "content": "Chicago is the third most populous city in the United States. Located on the shores of Lake Michigan, it is known for its architecture, food, and cultural attractions.",
        "metadata": {"type": "city_info", "city": "Chicago", "country": "USA"}
    })
    
    rag.add_document({
        "content": "International students in the USA need an F-1 visa to study at accredited colleges and universities. The visa application process requires an I-20 form from the educational institution.",
        "metadata": {"type": "visa_info", "visa_type": "F-1", "country": "USA"}
    })
    
    # Generate a response
    response = rag.generate_response("What visa do I need to study in the USA?")
    print(response)
