import requests
import time

API_URL = "http://35.200.185.69:8000/v1/autocomplete?query=a"


REQUESTS_COUNT = 500
DURATION = 300  

def send_requests():
    start_time = time.time()
    
    for i in range(REQUESTS_COUNT):
        response = requests.get(API_URL)
        print(f"Request {i+1}: Status Code {response.status_code}")

        # If we hit the rate limit (429), terminate and return the count
        if response.status_code == 429:
            print(f"Rate limit reached after {i+1} requests. Stopping.")
            return i + 1  # Return the number of requests made

        # Calculate remaining time per request to keep within 1-minute limit
        elapsed_time = time.time() - start_time
        remaining_time = (i + 1) * (DURATION / REQUESTS_COUNT) - elapsed_time

        if remaining_time > 0:
            time.sleep(remaining_time)  # Wait to maintain the request rate

    print("Completed 300 requests in 1 minute.")
    return REQUESTS_COUNT  # Return full count if all requests succeed

if __name__ == "__main__":
    total_requests_made = send_requests()
    print(f"Total requests made before stopping: {total_requests_made}")
