
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock dependencies
sys.modules["scraper"] = MagicMock()
sys.modules["productAnalyzer"] = MagicMock()
sys.modules["audioGeneration"] = MagicMock()
sys.modules["heygen"] = MagicMock()
sys.modules["facebook.client"] = MagicMock()
sys.modules["facebook.campaigns"] = MagicMock()
sys.modules["facebook.adsets"] = MagicMock()
sys.modules["facebook.ads"] = MagicMock()
sys.modules["facebook.media"] = MagicMock()

# Mock specific functions
with patch("facebook.campaigns.create_campaign", new_callable=AsyncMock) as mock_create_campaign, \
     patch("facebook.adsets.create_adset", new_callable=AsyncMock) as mock_create_adset, \
     patch("facebook.ads.create_video_ad", new_callable=AsyncMock) as mock_create_video_ad, \
     patch("facebook.media.upload_media_service", new_callable=MagicMock) as mock_upload_media:

    from server import app
    client = TestClient(app)

    def test_create_campaign():
        mock_create_campaign.return_value = {"id": "campaign_123", "success": True}
        
        response = client.post("/facebook/campaigns", json={
            "account_id": "123",
            "name": "Test Campaign",
            "objective": "OUTCOME_TRAFFIC",
            "access_token": "token"
        })
        
        assert response.status_code == 200
        assert response.json()["id"] == "campaign_123"
        mock_create_campaign.assert_called_once()

    def test_upload_media():
        mock_upload_media.return_value = {"image_hash": "hash_123"}
        
        # Create dummy file
        with open("test_image.jpg", "w") as f:
            f.write("dummy")
            
        with open("test_image.jpg", "rb") as f:
            response = client.post("/facebook/media/upload", 
                data={"account_id": "123", "media_type": "image", "access_token": "token"},
                files={"file": ("test_image.jpg", f, "image/jpeg")}
            )
            
        if os.path.exists("test_image.jpg"):
            os.remove("test_image.jpg")
            
        assert response.status_code == 200
        assert response.json()["image_hash"] == "hash_123"
        mock_upload_media.assert_called_once()

if __name__ == "__main__":
    try:
        test_create_campaign()
        test_upload_media()
        print("✅ Facebook Routes Tests Passed!")
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
