import requests
from typing import List, Tuple
import concurrent.futures
from tqdm import tqdm

def test_url(url: str) -> Tuple[str, bool, str]:
    """Test if a URL is accessible."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return url, True, "OK"
    except Exception as e:
        return url, False, str(e)

def validate_urls(urls_file: str) -> List[str]:
    """Validate URLs and return list of working URLs."""
    with open(urls_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    working_urls = []
    failed_urls = []

    print(f"Testing {len(urls)} URLs...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(test_url, url): url for url in urls}
        
        for future in tqdm(concurrent.futures.as_completed(future_to_url), total=len(urls)):
            url, success, message = future.result()
            if success:
                working_urls.append(url)
            else:
                failed_urls.append((url, message))

    print("\nResults:")
    print(f"Working URLs: {len(working_urls)}")
    if failed_urls:
        print("\nFailed URLs:")
        for url, message in failed_urls:
            print(f"- {url}: {message}")

    return working_urls

if __name__ == "__main__":
    working_urls = validate_urls("documents/urls.txt")
    
    # Save working URLs to a new file
    with open("documents/working_urls.txt", 'w') as f:
        for url in working_urls:
            f.write(f"{url}\n")
    print("\nWorking URLs saved to documents/working_urls.txt") 