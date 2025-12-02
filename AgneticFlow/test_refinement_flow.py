import asyncio
import os
import json
from dotenv import load_dotenv
from AgneticFlow.workflow_graph import AdCampaignWorkflow
from AgneticFlow.state_schema import WorkflowState

# Load environment variables
load_dotenv()

async def test_refinement_flow():
    print("Starting Refinement Flow Test...")
    
    # Initialize workflow
    workflow = AdCampaignWorkflow()
    
    # Mock initial state for Script Selection Test
    initial_state = {
        "current_step": "generate_scripts",
        "product_data": {"title": "Test Product"},
        "scripts": ["Script 1 content", "Script 2 content", "Script 3 content"],
        "messages": []
    }
    
    print("\n--- Test 1: Script Selection ---")
    initial_state["messages"].append({"role": "user", "content": "choose 2"})
    
    config = {"configurable": {"thread_id": "test_thread_refine"}}
    state = await workflow.app.ainvoke(initial_state, config)
    
    print(f"Step after 'choose 2': {state['current_step']}")
    print(f"Navigation Intent: {state.get('navigation_intent')}")
    print(f"Agent Message: {state.get('agent_message')}")
    
    if state['current_step'] == "select_script":
        print("SUCCESS: Correctly routed to select_script")
        print(f"Selected Script: {state.get('selected_script')}")
    else:
        print(f"FAILURE: Expected select_script, got {state['current_step']}")

    # Now simulate feedback
    print("\n--- Test 2: Script Refinement ---")
    # The previous step ended. Now user provides feedback.
    # We need to simulate the state after select_script finished.
    # In real flow, select_script returns, then route runs again?
    # No, select_script -> END. User inputs next message.
    
    state["messages"].append({"role": "user", "content": "make it funny"})
    state = await workflow.app.ainvoke(state, config)
    
    print(f"Step after 'make it funny': {state['current_step']}")
    print(f"Navigation Intent: {state.get('navigation_intent')}")
    
    if state['current_step'] == "refine_script":
        print("SUCCESS: Correctly routed to refine_script")
    else:
        print(f"FAILURE: Expected refine_script, got {state['current_step']}")

    print("\n--- Test 3: URL Restart Confirmation ---")
    # User enters URL mid-flow
    state["messages"].append({"role": "user", "content": "http://newproduct.com"})
    state = await workflow.app.ainvoke(state, config)
    
    print(f"Step after URL input: {state['current_step']}")
    print(f"Agent Message: {state.get('agent_message')}")
    
    if state['current_step'] == "confirm_restart":
        print("SUCCESS: Correctly routed to confirm_restart")
    else:
        print(f"FAILURE: Expected confirm_restart, got {state['current_step']}")
        
    # Confirm restart
    print("\n--- Test 4: Confirm Restart (Yes) ---")
    state["messages"].append({"role": "user", "content": "yes"})
    state = await workflow.app.ainvoke(state, config)
    
    print(f"Step after 'yes': {state['current_step']}")
    print(f"New URL: {state.get('url')}")
    
    if state['current_step'] == "scrape" and state.get('url') == "http://newproduct.com":
        print("SUCCESS: Correctly restarted to scrape with new URL")
    else:
        print(f"FAILURE: Expected scrape with new URL, got {state['current_step']} / {state.get('url')}")

    print("\n--- Test 5: Backtracking clears selection ---")
    # Reset state to have a selected script
    state["current_step"] = "select_script"
    state["selected_script"] = "Script 1"
    state["scripts"] = ["Script 1", "Script 2", "Script 3"]
    
    # Simulate user asking to regenerate scripts
    state["messages"].append({"role": "user", "content": "generate new scripts"})
    
    # We need to force the intent to generate_scripts for this test if the agent doesn't pick it up
    # But let's see if the agent picks it up. If not, we'll manually route.
    # Actually, let's just manually invoke the generate_scripts node logic via the graph
    # by setting intent to 'generate_scripts'
    
    # For testing purposes, we'll just check if running the workflow with "generate_scripts" intent clears it
    state["navigation_intent"] = "generate_scripts"
    state = await workflow.app.ainvoke(state, config)
    
    print(f"Step after backtracking: {state['current_step']}")
    print(f"Selected Script: {state.get('selected_script')}")
    
    if state['current_step'] == "generate_scripts" and state.get('selected_script') is None:
        print("SUCCESS: Backtracking cleared selected_script")
    else:
        print(f"FAILURE: selected_script not cleared. Got: {state.get('selected_script')}")

if __name__ == "__main__":
    asyncio.run(test_refinement_flow())
