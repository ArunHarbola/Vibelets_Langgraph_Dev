from dotenv import load_dotenv
import os
from config import Config
from orchestrator import AdCampaignAgent

load_dotenv()

def main():
    """Entry point"""

    required_keys = {
        "OPENAI_API_KEY": Config.OPENAI_API_KEY,
        "ELEVENLABS_API_KEY": Config.ELEVENLABS_API_KEY,
        "HEYGEN_API_KEY": Config.HEYGEN_API_KEY,
        "META_ACCESS_TOKEN": Config.META_ACCESS_TOKEN
    }

    missing_keys = [k for k, v in required_keys.items() if not v]

    if missing_keys:
        print("⚠️  Warning: Missing API keys:")
        for key in missing_keys:
            print(f"  - {key}")
        print("\nSet them as environment variables before running.")

        proceed = input("\nContinue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            return

    agent = AdCampaignAgent()
    agent.run()

if __name__ == "__main__":
    main()
