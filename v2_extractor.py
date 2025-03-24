import aiohttp
import asyncio
import heapq

API_URL = "http://35.200.185.69:8000/v2/autocomplete"  # Updated to v2 for alphanumeric results
HEADERS = {"User-Agent": "Mozilla/5.0"}

# API rate limit settings
MAX_REQUESTS_PER_MIN = 50
REQUEST_INTERVAL = 60 / MAX_REQUESTS_PER_MIN  

async def fetch_autocomplete_results(session, query, semaphore):
    """Fetch autocomplete suggestions asynchronously with rate limiting."""
    async with semaphore:  
        await asyncio.sleep(REQUEST_INTERVAL)  # Ensure API rate limit compliance
        try:
            async with session.get(API_URL, params={"query": query}, headers=HEADERS) as response:
                if response.status != 200:
                    print(f"Error status {response.status} for query '{query}'")
                    return []
                data = await response.json()
                # Check both possible API response keys
                results = data.get("results", data.get("suggestions", []))
                print(f"Debug - Raw response: {data}")  # Add debug info to see actual response
                return results
        except Exception as e:
            print(f"Error fetching '{query}': {e}")
            return []

def next_lexicographic_string(s):
    """Generate the next lexicographical string after `s` including alphanumeric characters."""
    if not s:
        return ""
    alphanumeric = "0123456789abcdefghijklmnopqrstuvwxyz"
    index = alphanumeric.find(s[-1])
    if index == -1:
        return s + '0'
    if index == len(alphanumeric) - 1:
        return s + '0'
    return s[:-1] + alphanumeric[index + 1]

async def scrape_autocomplete():
    """Efficiently scrape all words while respecting API limits."""
    priority_queue = []
    for c in "0123456789abcdefghijklmnopqrstuvwxyz":
        heapq.heappush(priority_queue, c)
    
    discovered_words = set()
    queried_prefixes = set()
    
    # Semaphore to control concurrent requests
    semaphore = asyncio.Semaphore(10)  # Allow 10 concurrent requests
    
    async with aiohttp.ClientSession() as session:
        with open("autocomplete_words.txt", "w") as f:
            while priority_queue:  
                prefix = heapq.heappop(priority_queue)
                
                if prefix in queried_prefixes:
                    continue
                    
                print(f"Querying prefix: '{prefix}'")
                queried_prefixes.add(prefix)
                
                suggestions = await fetch_autocomplete_results(session, prefix, semaphore)
                
                if not suggestions:
                    continue
                    
                new_words = [word for word in suggestions if word not in discovered_words]
                if new_words:
                    f.writelines(f"{word}\n" for word in new_words)
                    f.flush()  # Ensure immediate writing to file
                    discovered_words.update(new_words)
                    print(f"Found {len(new_words)} new words for '{prefix}'. Total words: {len(discovered_words)}")
                
                # Get prefixes from current suggestions
                for word in suggestions:
                    if len(prefix) < len(word):
                        next_prefix = word[:len(prefix) + 1]
                        if next_prefix not in queried_prefixes:
                            heapq.heappush(priority_queue, next_prefix)
                
                # Try the next possible prefix after the last suggestion
                if suggestions:
                    next_possible_prefix = next_lexicographic_string(prefix)
                    if next_possible_prefix and next_possible_prefix not in queried_prefixes:
                        heapq.heappush(priority_queue, next_possible_prefix)
    
    return sorted(discovered_words)

async def main():
    print("Starting autocomplete scraper...")
    await scrape_autocomplete()
    print("Scraping completed. Results saved to autocomplete_words.txt")

if __name__ == "__main__":
    asyncio.run(main())
