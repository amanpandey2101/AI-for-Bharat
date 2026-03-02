import boto3
from app.config import settings

kwargs = {
    "region_name": settings.AWS_REGION,
    "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
    "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY
}

client = boto3.client("bedrock-runtime", **kwargs)
response = client.converse_stream(
    modelId=settings.BEDROCK_MODEL_ID,
    messages=[{"role": "user", "content": [{"text": "Hello, how are you?"}]}]
)
for chunk in response.get("stream", []):
    if "contentBlockDelta" in chunk:
        print(chunk["contentBlockDelta"]["delta"]["text"], end="", flush=True)
print("\nDone")
