import os
from app.config import settings
import boto3

kwargs = {
    "region_name": settings.AWS_REGION,
    "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
    "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY
}

client = boto3.client("bedrock-agent-runtime", **kwargs)

try:
    response = client.retrieve_and_generate(
        input={"text": "Hello"},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": settings.BEDROCK_KB_ID,
                "modelArn": f"arn:aws:bedrock:{settings.AWS_REGION}::foundation-model/{settings.BEDROCK_MODEL_ID}"
            }
        }
    )
    print("SUCCESS:")
    print(response.get("output", {}).get("text"))
except Exception as e:
    print(f"Error: {e}")
