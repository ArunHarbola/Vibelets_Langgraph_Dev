import asyncio
import sys
import os
from typing import Dict, List

# Add AgneticFlow to path
sys.path.append(os.path.abspath("AgneticFlow"))

from agents import ScriptGenerationAgent
from dotenv import load_dotenv

load_dotenv()

async def verify():
    print("Initializing ScriptGenerationAgent...")
    try:
        agent = ScriptGenerationAgent()
    except Exception as e:
        print(f"Error initializing agent: {e}")
        return

    # Mock data
    product_data = {
        "title": "Eco-Friendly Water Bottle",
        "description": "A durable, reusable water bottle made from recycled materials. Keeps drinks cold for 24 hours."
    }
    analysis = {
        "target_audience": "Environmentally conscious millennials, hikers, gym-goers",
        "usps": "Sustainable, durable, temperature retention",
        "marketing_angles": "Save the planet, stay hydrated in style"
    }

    print("Generating scripts...")
    with open("verify_scripts_result.txt", "w", encoding="utf-8") as f:
        try:
            scripts = await agent.generate_scripts(product_data, analysis)
            
            f.write(f"Generated {len(scripts)} scripts.\n")
            
            if len(scripts) == 3:
                f.write("SUCCESS: Exactly 3 scripts generated.\n")
            else:
                f.write(f"FAILURE: Expected 3 scripts, got {len(scripts)}.\n")
                
            for i, script in enumerate(scripts, 1):
                f.write(f"\n--- Script {i} ---\n")
                f.write(script + "\n")
                
        except Exception as e:
            f.write(f"Error generating scripts: {e}\n")
            import traceback
            traceback.print_exc(file=f)

if __name__ == "__main__":
    asyncio.run(verify())
