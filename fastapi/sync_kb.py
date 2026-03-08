import os
import sys

# Add the parent directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.bedrock_agent import agent_service

def force_sync():
    print("🚀 Triggering manual Knowledge Base sync...")
    success = agent_service.sync_knowledge_base()
    if success:
        print("✅ Sync job started successfully! Bedrock is now indexing your 'decisions/' folder.")
        print("Please wait 1-2 minutes for indexing to complete.")
    else:
        print("❌ Sync job failed. Check your BEDROCK_KB_ID in .env")

if __name__ == "__main__":
    force_sync()
