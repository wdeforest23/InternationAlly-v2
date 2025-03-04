import os
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import openai

# Load environment variables
load_dotenv()

# Get API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

class RAGSystem:
    """
    Retrieval-Augmented Generation (RAG) system for enhancing AI responses
    with relevant information from a knowledge base.
    """
    
    def __init__(self, knowledge_base_path: Optional[str] = None):
        """
        Initialize the RAG system
        
        Args:
            knowledge_base_path: Path to the knowledge base file (JSON)
        """
        self.knowledge_base = []
        self.embeddings = []
        
        # Load knowledge base if provided
        if knowledge_base_path and os.path.exists(knowledge_base_path):
            self.load_knowledge_base(knowledge_base_path)
    
    def load_knowledge_base(self, knowledge_base_path: str) -> None:
        """
        Load knowledge base from a JSON file
        
        Args:
            knowledge_base_path: Path to the knowledge base file (JSON)
        """
        try:
            with open(knowledge_base_path, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
            
            # Generate embeddings for the knowledge base
            self.generate_embeddings()
        except Exception as e:
            print(f"Error loading knowledge base: {str(e)}")
            self.knowledge_base = []
            self.embeddings = []
    
    def add_document(self, document: Dict[str, Any]) -> None:
        """
        Add a document to the knowledge base
        
        Args:
            document: Document to add (must have 'content' and 'metadata' fields)
        """
        if 'content' not in document or 'metadata' not in document:
            raise ValueError("Document must have 'content' and 'metadata' fields")
        
        self.knowledge_base.append(document)
        
        # Generate embedding for the new document
        embedding = self.get_embedding(document['content'])
        if self.embeddings:
            self.embeddings = np.vstack([self.embeddings, embedding])
        else:
            self.embeddings = np.array([embedding])
    
    def generate_embeddings(self) -> None:
        """
        Generate embeddings for all documents in the knowledge base
        """
        if not self.knowledge_base:
            self.embeddings = []
            return
        
        self.embeddings = []
        for doc in self.knowledge_base:
            embedding = self.get_embedding(doc['content'])
            self.embeddings.append(embedding)
        
        self.embeddings = np.array(self.embeddings)
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for a text using OpenAI's embedding API
        
        Args:
            text: Text to get embedding for
        
        Returns:
            Embedding vector
        """
        try:
            response = openai.Embedding.create(
                input=text,
                model="text-embedding-ada-002"
            )
            embedding = response['data'][0]['embedding']
            return np.array(embedding)
        except Exception as e:
            print(f"Error getting embedding: {str(e)}")
            # Return a zero vector as fallback
            return np.zeros(1536)  # Default dimension for OpenAI embeddings
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant documents for a query
        
        Args:
            query: Query text
            top_k: Number of documents to retrieve
        
        Returns:
            List of relevant documents
        """
        if not self.knowledge_base or not self.embeddings.size:
            return []
        
        # Get embedding for the query
        query_embedding = self.get_embedding(query)
        
        # Calculate similarity scores
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        
        # Get indices of top_k most similar documents
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return top_k documents
        return [
            {
                "content": self.knowledge_base[i]['content'],
                "metadata": self.knowledge_base[i]['metadata'],
                "similarity": float(similarities[i])
            }
            for i in top_indices
        ]
    
    def generate_response(self, query: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response to a query using RAG
        
        Args:
            query: User query
            system_prompt: Optional system prompt to guide the response
        
        Returns:
            Generated response
        """
        # Retrieve relevant documents
        relevant_docs = self.retrieve(query)
        
        # Construct context from relevant documents
        context = ""
        for i, doc in enumerate(relevant_docs):
            context += f"\nDocument {i+1}:\n{doc['content']}\n"
        
        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = (
                "You are a helpful assistant for international students and immigrants. "
                "Use the provided context to answer the user's question. "
                "If the context doesn't contain relevant information, say so and provide general guidance."
            )
        
        # Generate response using OpenAI
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I'm sorry, I couldn't generate a response at this time."
    
    def save_knowledge_base(self, output_path: str) -> None:
        """
        Save the knowledge base to a JSON file
        
        Args:
            output_path: Path to save the knowledge base
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, indent=2)
        except Exception as e:
            print(f"Error saving knowledge base: {str(e)}")

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
