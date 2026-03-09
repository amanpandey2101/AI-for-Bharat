import os
import sys
import time
import json

try:
    import pandas as pd
    import phoenix as px
    import boto3
    from phoenix.otel import register
    from openinference.instrumentation.bedrock import BedrockInstrumentor
except ImportError as e:
    print(f"Missing dependency: {e}")
    sys.exit(1)

# Ensure FastAPI is on the path
repo_root = os.path.dirname(os.path.abspath(__file__))
fastapi_dir = os.path.join(repo_root, "fastapi")
sys.path.append(fastapi_dir)

def setup_tracing():
    print("Setting up OpenInference tracing...")
    
    # We'll use a unique project name to avoid confusion
    project_name = "Hackathon-Benchmark"
    
    # Register the tracer provider with Phoenix
    try:
        # Using register() which sets everything up for Phoenix
        register(
            project_name=project_name,
            endpoint="http://localhost:6006/v1/traces"
        )
        
        # Instrument Bedrock AFTER registration
        BedrockInstrumentor().instrument()
        print(f"Tracing configured for project: {project_name}")
        return project_name
    except Exception as e:
        print(f"Error during tracing setup: {e}")
        return "default"

def run_benchmark_queries():
    print("\nRunning benchmark queries to populate Phoenix...")
    
    # Temporarily change directory to load .env correctly via settings
    original_cwd = os.getcwd()
    os.chdir(fastapi_dir)
    
    try:
        from app.config import settings
        region = settings.AWS_REGION or 'us-west-2'
        model_id = settings.BEDROCK_MODEL_ID or 'meta.llama3-1-8b-instruct-v1:0'
        
        # Use credentials from settings
        credentials = {}
        if getattr(settings, "AWS_ACCESS_KEY_ID", None):
            credentials["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        if getattr(settings, "AWS_SECRET_ACCESS_KEY", None):
            credentials["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            
    except Exception as e:
        print(f"Could not load settings: {e}")
        region = 'us-west-2'
        model_id = 'meta.llama3-1-8b-instruct-v1:0'
        credentials = {}
    finally:
        os.chdir(original_cwd)

    print(f"Using Bedrock region: {region}, model: {model_id}")
    
    # Create Bedrock client AFTER instrumentation
    try:
        client = boto3.client('bedrock-runtime', region_name=region, **credentials)
    except Exception as e:
        print(f"Error creating bedrock client: {e}")
        return

    queries = [
        "What is Memora.dev?",
        "Explain AI-powered institutional memory.",
        "How can AI prevent organizational amnesia?",
        "Summarize the value of tracking decision rationale.",
        "List 3 key features of an AI-driven memory platform."
    ]

    for i, q in enumerate(queries):
        try:
            start_time = time.time()
            # Bedrock converse is instrumented
            response = client.converse(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": q}]}],
                inferenceConfig={"maxTokens": 100, "temperature": 0.5}
            )
            duration = time.time() - start_time
            print(f"Query {i+1} completed in {duration:.2f}s")
        except Exception as e:
            print(f"Error querying bedrock for query {i+1}: {e}")
            if "AccessDeniedException" in str(e):
                print("AWS Access Denied. Check credentials in .env")

def generate_report(project_name):
    print("\nWaiting for traces to flush (8 seconds)...")
    time.sleep(8)
    
    print(f"Fetching traces from Phoenix for project: {project_name}")
    try:
        # Connect to localized Phoenix
        px_client = px.Client(endpoint="http://localhost:6006")
        
        # Fetch spans specifically for our project
        df = px_client.get_spans_dataframe(project_name=project_name)
    except Exception as e:
        print(f"Error connecting to Phoenix: {e}")
        return
        
    if df.empty:
        print(f"No spans found in Phoenix project '{project_name}'.")
        print("Checking for ANY spans in Phoenix...")
        try:
            df_any = px_client.get_spans_dataframe()
            if not df_any.empty:
                print(f"Found {len(df_any)} spans in other/any projects.")
                df = df_any
            else:
                print("Phoenix database is empty. Check if server is running on 6006.")
                return
        except:
            return

    # Filter for LLM spans
    llm_spans = df[df['span_kind'] == 'LLM'] if 'span_kind' in df.columns else df
    
    if llm_spans.empty:
        print("No LLM-specific spans found. Using all available spans for metrics.")
        llm_spans = df

    # Define token columns for metrics
    token_cols = [c for c in llm_spans.columns if 'token_count' in c.lower()]

    # prepares costs and metrics
    # Llama 3.1 8B prices (approximate)
    INPUT_PRICE_PER_1K = 0.00005
    OUTPUT_PRICE_PER_1K = 0.00015
    
    # Robust token extraction
    prompt_col = next((c for c in token_cols if 'prompt' in c.lower()), None)
    completion_col = next((c for c in token_cols if 'completion' in c.lower()), None)
    
    total_input_tokens = llm_spans[prompt_col].sum() if prompt_col else 0
    total_output_tokens = llm_spans[completion_col].sum() if completion_col else 0
    
    total_cost = (total_input_tokens / 1000 * INPUT_PRICE_PER_1K) + (total_output_tokens / 1000 * OUTPUT_PRICE_PER_1K)
    
    # Calculate Avg TPS
    # Use latency in seconds
    lat_col = 'latency_ms' if 'latency_ms' in llm_spans.columns else ('lat' if 'lat' in llm_spans.columns else None)
    
    if lat_col:
        total_latency_sec = llm_spans[lat_col].sum() / 1000
    else:
        total_latency_sec = 0

    avg_tps = total_output_tokens / total_latency_sec if total_latency_sec > 0 else 0

    # Prepare markdown report
    report_md = f"""# AI-for-Bharat Performance Benchmark

*Generated using Arize-Phoenix LLM Tracing*

## Overview
This report benchmarks the performance of Amazon Bedrock models used in the system, instrumented with OpenInference.

### Summary Metrics
* **Total LLM Inferences tracked:** {len(llm_spans)}
* **Total Estimated Cost:** ${total_cost:.6f}
* **Avg Throughput (TPS):** {avg_tps:.2f} tokens/sec
"""

    # Extract metrics
    # Latency estimation
    if 'latency_ms' in llm_spans.columns:
        avg_lat = llm_spans['latency_ms'].mean()
        p95_lat = llm_spans['latency_ms'].quantile(0.95)
        report_md += f"* **Average Latency:** {avg_lat:.2f} ms\n"
        report_md += f"* **P95 Latency:** {p95_lat:.2f} ms\n"
    elif 'start_time' in llm_spans.columns and 'end_time' in llm_spans.columns:
        llm_spans['lat'] = (pd.to_datetime(llm_spans['end_time']) - pd.to_datetime(llm_spans['start_time'])).dt.total_seconds() * 1000
        avg_lat = llm_spans['lat'].mean()
        report_md += f"* **Average Latency:** {avg_lat:.2f} ms\n"


    # Token counts
    for col in token_cols:
        name = col.split('.')[-1].replace('_', ' ').title()
        avg_tokens = llm_spans[col].mean()
        report_md += f"* **Average {name}:** {avg_tokens:.1f}\n"

    report_md += "\n## Sample Benchmarks\n\n"
    
    # Columns to show in table
    table_cols = []
    if 'name' in llm_spans.columns: table_cols.append('name')
    if 'latency_ms' in llm_spans.columns: table_cols.append('latency_ms')
    elif 'lat' in llm_spans.columns: table_cols.append('lat')
    
    important_tokens = [c for c in token_cols if 'total' in c.lower() or 'prompt' in c.lower()]
    table_cols.extend(important_tokens)
    
    if table_cols:
        sample_df = llm_spans[table_cols].head(5)
        report_md += sample_df.to_markdown(index=False)
        
    report_path = os.path.join(repo_root, "benchmark_report.md")
    with open(report_path, "w") as f:
        f.write(report_md)
        
    print(f"\nBenchmark report successfully generated at: {report_path}")
    print("You can add these metrics to your hackathon PPT slide!")

if __name__ == "__main__":
    p_name = setup_tracing()
    run_benchmark_queries()
    generate_report(p_name)
