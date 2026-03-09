import time
import random
import threading
import requests
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
TARGET_HOST = "https://d1uknmi6v4v72d.cloudfront.net" # Change to your live URL
VIRTUAL_USERS = 100
DURATION_SECONDS = 30
# ---------------------

stats = {
    "total_requests": 0,
    "success": 0,
    "failure": 0,
    "latencies": []
}
stats_lock = threading.Lock()

def simulate_user():
    """Function representing a single virtual user's actions."""
    end_time = time.time() + DURATION_SECONDS
    
    endpoints = [
        {"path": "/decisions/", "method": "GET", "name": "List Decisions"},
        {"path": "/health", "method": "GET", "name": "Health Check"},
        {"path": "/decisions/search", "method": "POST", "name": "Search", "json": {"question": "Why did we use S3?"}}
    ]
    
    while time.time() < end_time:
        action = random.choice(endpoints)
        url = f"{TARGET_HOST}{action['path']}"
        
        start = time.time()
        try:
            if action["method"] == "GET":
                resp = requests.get(url, timeout=10)
            else:
                resp = requests.post(url, json=action.get("json"), timeout=10)
            
            latency = (time.time() - start) * 1000 # to ms
            
            with stats_lock:
                stats["total_requests"] += 1
                stats["latencies"].append(latency)
                if resp.status_code < 400:
                    stats["success"] += 1
                else:
                    stats["failure"] += 1
                    
        except Exception as e:
            with stats_lock:
                stats["total_requests"] += 1
                stats["failure"] += 1
        
        # Thinking time
        time.sleep(random.uniform(0.5, 2.0))

def run_benchmark():
    print(f"🚀 Starting benchmark: {VIRTUAL_USERS} users for {DURATION_SECONDS}s at {TARGET_HOST}")
    
    with ThreadPoolExecutor(max_workers=VIRTUAL_USERS) as executor:
        for _ in range(VIRTUAL_USERS):
            executor.submit(simulate_user)
            
    # Final Report
    print("\n" + "="*30)
    print("📊 PERFORMANCE REPORT")
    print("="*30)
    
    total = stats["total_requests"]
    if total == 0:
        print("No requests made.")
        return

    avg_latency = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0
    stats["latencies"].sort()
    p95 = stats["latencies"][int(len(stats["latencies"]) * 0.95)] if stats["latencies"] else 0
    
    print(f"Total Requests: {total}")
    print(f"Successful:     {stats['success']} ({(stats['success']/total)*100:.1f}%)")
    print(f"Failed:         {stats['failure']} ({(stats['failure']/total)*100:.1f}%)")
    print(f"Avg Latency:    {avg_latency:.2f} ms")
    print(f"P95 Latency:    {p95:.2f} ms")
    print(f"Throughput:     {total/DURATION_SECONDS:.2f} req/s")
    print("="*30)

if __name__ == "__main__":
    run_benchmark()
