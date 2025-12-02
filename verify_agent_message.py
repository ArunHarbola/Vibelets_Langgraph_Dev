import asyncio
import sys
import os

# Add AgneticFlow to path
sys.path.append(os.path.abspath("AgneticFlow"))

from workflow_graph import AdCampaignWorkflow

async def verify():
    print("Initializing workflow...")
    try:
        workflow = AdCampaignWorkflow()
    except Exception as e:
        print(f"Error initializing workflow: {e}")
        return

    # Create a mock state
    state = {
        "current_step": "scrape",
        "messages": [{"role": "user", "content": "https://example.com"}],
        "url": "https://example.com"
    }
    
    # Run the route node directly to check agent message generation
    # The route node is what calls the guide agent
    with open("verify_result.txt", "w", encoding="utf-8") as f:
        f.write("Running route node...\n")
        try:
            result = await workflow._route_node(state)
            
            f.write("\nResult:\n")
            f.write(str(result))
            
            if "agent_message" in result and result["agent_message"]:
                f.write("\n\nSUCCESS: agent_message found!\n")
                f.write(f"Message: {result['agent_message']}\n")
            else:
                f.write("\n\nFAILURE: agent_message not found or empty.\n")
                
        except Exception as e:
            f.write(f"\nError running route node: {e}\n")
            import traceback
            traceback.print_exc(file=f)

if __name__ == "__main__":
    asyncio.run(verify())
