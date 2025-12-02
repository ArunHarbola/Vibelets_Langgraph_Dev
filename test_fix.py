import requests
import uuid

BASE_URL = "http://localhost:8000"

def test_url_reflection():
    thread_id = str(uuid.uuid4())
    print(f"Testing with thread_id: {thread_id}")

    # 1. Send a URL message
    url = "https://www.example.com/product/123"
    payload = {
        "thread_id": thread_id,
        "message": url,
        "navigation_intent": "scrape" # Simulate what the frontend might send or infer
    }
    
    print(f"Sending URL: {url}")
    try:
        response = requests.post(f"{BASE_URL}/api/workflow/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Check the agent message in the response (this comes from the route node)
        # Note: The actual response structure depends on what /api/workflow/chat returns.
        # Based on server_langgraph.py, it returns state, current_step, etc.
        # The route node returns {navigation_intent, agent_message} which updates the state?
        # Wait, /api/workflow/chat calls workflow.run_step.
        # The route node is the entry point. It returns a dict.
        # If route returns {navigation_intent, agent_message}, that updates the state.
        # But the response from run_step is the final state after the step execution.
        # If route returns 'scrape', it goes to scrape node.
        # The scrape node updates state['url'].
        # BUT, the issue was about the *immediate* response or the guidance.
        # The route node calculates guidance *before* returning the next step.
        # Let's see if we can find the agent_message in the returned state or if it's just used for streaming?
        # Ah, the route node returns a dict that updates the state. So 'agent_message' should be in the state.
        
        state = data.get("state", {})
        agent_message = state.get("agent_message")
        print(f"Full Response Data: {data}")
        print(f"Agent Message: {agent_message}")
        
        if agent_message and ("http" in str(agent_message) or "analyzing" in str(agent_message).lower() or "scraping" in str(agent_message).lower()):
             print("SUCCESS: URL reflected in agent message.")
        else:
             print("WARNING: URL might not be reflected. Check message content.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_url_reflection()
