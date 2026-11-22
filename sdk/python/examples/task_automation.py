"""Example script: Automated task creation and sync using FocusBoard Python SDK."""
from focusboard_sdk.client import FocusBoardClient

def main():
    # Replace with your actual live API Key
    client = FocusBoardClient(api_key="fb_live_sample_key_12345")

    print("Fetching existing tasks...")
    try:
        tasks = client.list_tasks(limit=10)
        print(f"Retrieved {len(tasks)} tasks.")

        # Create a new automated task
        new_task = client.create_task(
            title="Automated Pipeline Run - Release v2.5",
            description="Created by CI/CD bot via FocusBoard SDK",
            priority="high",
            category="DevOps",
            idempotency_key="release-v2.5-deploy-task"
        )
        print(f"Created task: {new_task['id']} - {new_task['title']}")

        # Update task status
        updated = client.update_task(new_task['id'], status="in_progress")
        print(f"Updated task status to: {updated['status']}")

    except Exception as e:
        print(f"SDK Error: {e}")

if __name__ == "__main__":
    main()
