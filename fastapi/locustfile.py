from locust import HttpUser, task, between
import random
import uuid

class MemoraUser(HttpUser):
    wait_time = between(1, 2)
    
    # Normally you'd need an auth token, but for a local benchmark we can simulate 
    # or skip auth if you've disabled it for testing.
    # header = {"Authorization": "Bearer YOUR_TOKEN"}

    @task(3)
    def view_activity(self):
        """Simulate a user checking the activity feed."""
        self.client.get("/decisions/", name="List Decisions")

    @task(2)
    def check_stats(self):
        """Simulate a user checking the dashboard stats."""
        self.client.get("/decisions/stats/overview", name="Get Stats")

    @task(1)
    def search_decisions(self):
        """Simulate a user performing a semantic search."""
        self.client.post("/decisions/search", json={
            "question": "Why did we choose DynamoDB?"
        }, name="Semantic Search")

    @task(4)
    def simulate_slack_webhook(self):
        """Simulate a burst of Slack messages hitting the ingestion endpoint."""
        # This tests the 'Passive Ingestion' performance
        self.client.post("/webhooks/slack", json={
            "token": "verification_token",
            "team_id": "T01234567",
            "api_app_id": "A01234567",
            "event": {
                "type": "message",
                "user": "U01234567",
                "text": "We should use S3 for long-term storage of our logs.",
                "ts": str(random.random()),
                "channel": "C01234567",
                "event_ts": str(random.random()),
            },
            "type": "event_callback",
        }, name="Slack Webhook Ingestion")
