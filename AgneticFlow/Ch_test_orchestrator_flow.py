
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from dotenv import load_dotenv
load_dotenv()
# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock dependencies
sys.modules["scraper"] = MagicMock()
sys.modules["productAnalyzer"] = MagicMock()
sys.modules["audioGeneration"] = MagicMock()
sys.modules["heygen"] = MagicMock()
sys.modules["facebook.media"] = MagicMock()
sys.modules["facebook.ads"] = MagicMock()

from orchestrator import AdCampaignAgent

def test_orchestrator_run():
    # Setup mocks
    agent = AdCampaignAgent()
    agent.scraper.scrape_url.return_value = {"title": "Test Product", "description": "Desc"}
    agent.analyzer.analyze_product_interactive.return_value = {}
    agent.analyzer.generate_ad_scripts_interactive.return_value = ["Script 1"]
    agent.analyzer.refine_selected_script_interactive.return_value = "Final Script"
    agent.voice_gen.generate_voice.return_value = "audio.mp3"
    
    # Mock external services
    with patch("facebook.media.upload_media_service", new_callable=MagicMock) as mock_upload_media, \
         patch("facebook.ads.create_image_ad", new_callable=AsyncMock) as mock_create_image_ad, \
         patch("builtins.input", side_effect=[
             "http://test.com", # URL
             "confirm", # Analysis
             "confirm", # Scripts
             "1", # Script choice
             "confirm", # Script tweak
             "", # Audio URL (skip heygen)
             "test_folder", # Folder path
             "12345" # AdSet ID
         ]), \
         patch("os.listdir", return_value=["test.jpg"]), \
         patch("os.path.exists", return_value=True), \
         patch("os.getenv", side_effect=lambda k: "dummy_val" if k in ["META_PAGE_ID", "META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"] else None):
        
        mock_upload_media.return_value = {"image_hash": "hash_123"}
        mock_create_image_ad.return_value = {"id": "ad_123"}

        try:
            agent.run()
            print("✅ Orchestrator Run Completed")
            
            # Verify Meta upload calls
            mock_upload_media.assert_called()
            mock_create_image_ad.assert_called()
            
        except Exception as e:
            print(f"❌ Orchestrator Run Failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_orchestrator_run()
