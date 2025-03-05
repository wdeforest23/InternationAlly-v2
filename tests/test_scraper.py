import os
from app.utils.rag_system import RAGSystem

def test_url_scraping():
    rag = RAGSystem()
    test_url = "https://internationalaffairs.uchicago.edu/students/current-students/maintaining-a-full-time-course-load"
    
    result = rag.fetch_and_process_url(test_url)
    if result:
        print("Successfully scraped URL!")
        print(f"Title: {result['title']}")
        print("\nFirst 500 characters of content:")
        print(result['content'][:500])
        return True
    return False

if __name__ == "__main__":
    test_url_scraping() 