import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv()

# Setup correct import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.integrations.models import get_integrations_table, IntegrationModel
from app.integrations.slack_backfill import run_backfill_for_channel

def main():
    table = get_integrations_table()
    
    # Simple scan to find any slack integration for testing
    response = table.scan(
        FilterExpression="platform = :p",
        ExpressionAttributeValues={":p": "slack"}
    )
    items = response.get("Items", [])
    
    if not items:
        print("No slack integrations found in the database.")
        sys.exit(0)
        
    for item in items:
        integration = IntegrationModel.from_dynamo_item(item)
        print(f"Found Slack integration for user: {integration.user_id}")
        
        # Look for connected resources (channels)
        if not integration.resources:
            print(f"  User has no connected Slack channels.")
            continue
            
        for resource in integration.resources:
            if resource.resource_type == "channel":
                print(f"  Starting manual backfill test for channel: {resource.resource_id} ({resource.resource_name})")
                
                # Run the backfill synchronously for debugging
                run_backfill_for_channel(
                    access_token=integration.access_token,
                    channel_id=resource.resource_id,
                    user_id=integration.user_id
                )
                print(f"  Finished test for {resource.resource_name}")
                sys.exit(0) # Just test one

if __name__ == "__main__":
    main()
