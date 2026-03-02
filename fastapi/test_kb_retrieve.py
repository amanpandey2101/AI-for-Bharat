import os
from app.config import settings
import boto3
import json

kwargs = {
    "region_name": settings.AWS_REGION,
    "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
    "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY
}

client = boto3.client("bedrock-agent-runtime", **kwargs)

try:
    print("Testing Retrieve API directly to see if KB has data...")
    response = client.retrieve(
        knowledgeBaseId=settings.BEDROCK_KB_ID,
        retrievalQuery={"text": "decision architecture frontend backend typescript"},
        retrievalConfiguration={
            "vectorSearchConfiguration": {
                "numberOfResults": 5
            }
        }
    )
    results = response.get("retrievalResults", [])
    print(f"Found {len(results)} results in Knowledge Base.")
    for result in results:
        print(f"- {result['content']['text'][:100]}...")
except Exception as e:
    print(f"Error: {e}")
