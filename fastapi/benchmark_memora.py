import time
import threading
import requests
import random
import statistics

# --- CONFIGURATION ---
BASE_URL = "https://d1uknmi6v4v72d.cloudfront.net" # Change to http://localhost:8000 for local
TOTAL_USERS = 100
REQUESTS_PER_USER = 5
CONCURRENCY = 20 # How many users run at the exact same time

# --- LOGGING STATS ---
results = []
errors = 0

def simulate_user(user_id):
    global errors
    for i in range(REQUESTS_PER_USER):
        # Weighted random selection of endpoints
        choice = random.random()
        try:
            start_time = time.time()
            if choice < 0.4:
                # Public Health Check
                resp = requests.get(f"{BASE_URL}/health", timeout=10)
            elif choice < 0.7:
                # Root Message
                resp = requests.get(f"{BASE_URL}/", timeout=10)
            else:
                # Simulate Slack Webhook Ingestion
                resp = requests.post(f"{BASE_URL}/webhooks/slack", json={
                    "type": "event_callback",
                    "event": {"type": "message", "text": "Benchmark test", "ts": str(time.time()), "channel": "C123"}
                }, timeout=10)
            
            latency = (time.time() - start_time) * 1000 # convert to ms
            results.append(latency)
            
            # Note: 401/404 are still "successful" connections to the server
            if resp.status_code >= 500:
                errors += 1
                
        except Exception as e:
            errors += 1
            print(f"User {user_id} error: {e}")
        
        # Small random sleep to simulate human-like behavior
        time.sleep(random.uniform(0.1, 0.5))

def run_benchmark():
    print(f"🚀 Starting Memora Benchmark...")
    print(f"📡 Target: {BASE_URL}")
    print(f"👥 Simulating {TOTAL_USERS} Virtual Users ({TOTAL_USERS * REQUESTS_PER_USER} total requests)...")
    
    threads = []
    start_all = time.time()
    
    # Run in batches to maintain concurrency
    for i in range(TOTAL_USERS):
        t = threading.Thread(target=simulate_user, args=(i,))
        threads.append(t)
        t.start()
        
        # Throttling the 'spawn' rate a bit
        if len(threads) % CONCURRENCY == 0:
            time.sleep(0.5)

    for t in threads:
        t.join()
    
    total_duration = time.time() - start_all
    
    # --- REPORT ---
    print("\n" + "="*40)
    print("📈 MEMORA PERFORMANCE REPORT")
    print("="*40)
    print(f"Total Requests:    {len(results)}")
    print(f"Failed Requests:   {errors}")
    print(f"Success Rate:      {((len(results)-errors)/len(results))*100:.1f}%")
    print(f"Total Time:        {total_duration:.2f} seconds")
    print(f"Throughput:        {len(results)/total_duration:.2f} req/sec")
    print("-" * 40)
    print(f"Minimum Latency:   {min(results):.2f} ms")
    print(f"Maximum Latency:   {max(results):.2f} ms")
    print(f"Average Latency:   {statistics.mean(results):.2f} ms")
    print(f"Median Latency:    {statistics.median(results):.2f} ms")
    print(f"95th Percentile:   {statistics.quantiles(results, n=20)[18]:.2f} ms")
    print("="*40)

if __name__ == "__main__":
    run_benchmark()
