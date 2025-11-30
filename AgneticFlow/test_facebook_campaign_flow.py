"""
Test script for Facebook Ad Campaign AgentFlow
Tests the complete flow from authentication to campaign publishing
"""
import requests
import json
import time
import os
from dotenv import load_dotenv
FACEBOOK_ACCESS_TOKEN='EAAQeYqt2zH4BQMNm9RRLNJAuAfnqQ72wfdNFJ2WxbL9XhPlHeBVo41OjpTvkZAEIN0ySZCyHf3lC2f1YiQJ32itKRQXq6Yz2xt5RNsKk2RXryCEGxhSbAaUgLaLwKrVL7uu11scZBnSRWoLvqPkwZBePpDhz2xzMUjUads91cEH6bYZBwkO5ZBqtDavfL0nZARjSz3z'
# Load environment variables
load_dotenv()

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_facebook_campaign_flow():
    """Test the complete Facebook ad campaign flow"""
    
    print("=" * 60)
    print("Facebook Ad Campaign AgentFlow - Test Script")
    print("=" * 60)
    
    # Initialize thread_id
    thread_id = None
    
    # Step 1: Authenticate with Facebook
    print("\n[Step 1] Authenticating with Facebook...")
    
    # Get access token - try environment variable first, then hardcoded global
    access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
    
    # If not in environment, try to get from module-level variable
    if not access_token:
        try:
            import sys
            current_module = sys.modules[__name__]
            if hasattr(current_module, 'FACEBOOK_ACCESS_TOKEN'):
                access_token = getattr(current_module, 'FACEBOOK_ACCESS_TOKEN')
        except:
            pass
    
    if not access_token:
        print("✗ Error: FACEBOOK_ACCESS_TOKEN not found")
        print("  Please set it in your .env file or define it in the script")
        return
    
    auth_response = requests.post(
        f"{BASE_URL}/api/facebook/authenticate",
        json={
            "access_token": access_token,
            "thread_id": thread_id
        }
    )
    
    if auth_response.status_code == 200:
        auth_data = auth_response.json()
        thread_id = auth_data.get("thread_id")
        print(f"✓ Authentication successful!")
        print(f"  Thread ID: {thread_id}")
        
        # Check for errors in the state
        state = auth_data.get("state", {})
        if state and state.get("error"):
            print(f"  ✗ Error: {state['error']}")
            return
        
        # Get user_id and ad_accounts from the response
        user_id = auth_data.get("user_id") or (state.get("facebook_user_id") if state else None)
        ad_accounts = auth_data.get("ad_accounts") or (state.get("facebook_ad_accounts") if state else [])
        
        print(f"  User ID: {user_id}")
        print(f"  Ad Accounts: {len(ad_accounts) if ad_accounts else 0}")
        
        if not ad_accounts:
            print(f"  ⚠️  Warning: No ad accounts found. Check your Facebook access token.")
            print(f"  Response: {json.dumps(auth_data, indent=2)}")
            return
    else:
        print(f"✗ Authentication failed: {auth_response.status_code}")
        print(auth_response.text)
        return
    
    # Step 2: Select Ad Account
    print("\n[Step 2] Selecting ad account...")
    
    # Use ad_accounts from previous step (already extracted)
    if not ad_accounts:
        print("✗ No ad accounts found")
        return
    
    selected_account_id = ad_accounts[0].get("id", "").replace("act_", "")
    
    account_response = requests.post(
        f"{BASE_URL}/api/facebook/select_account",
        json={
            "account_id": selected_account_id,
            "thread_id": thread_id
        }
    )
    
    if account_response.status_code == 200:
        account_data = account_response.json()
        print(f"✓ Ad account selected!")
        print(f"  Account: {account_data.get('selected_account', {}).get('name')}")
    else:
        print(f"✗ Account selection failed: {account_response.status_code}")
        return
    
    # Step 3: List Available Media
    print("\n[Step 3] Listing available media...")
    media_response = requests.get(
        f"{BASE_URL}/api/facebook/media",
        params={"thread_id": thread_id}
    )
    
    if media_response.status_code == 200:
        media_data = media_response.json()
        available_media = media_data.get("available_media", [])
        print(f"✓ Found {len(available_media)} media files")
        
        for i, media in enumerate(available_media[:5]):  # Show first 5
            print(f"  {i+1}. {media.get('filename')} ({media.get('type')})")
        
        if not available_media:
            print("✗ No media files found. Please generate images/videos first.")
            return
    else:
        print(f"✗ Media listing failed: {media_response.status_code}")
        return
    
    # Step 4: Select Media
    print("\n[Step 4] Selecting media for campaign...")
    
    # Select first media (preferably video)
    selected_media = None
    for media in available_media:
        if media.get("type") == "video":
            selected_media = media
            break
    
    if not selected_media and available_media:
        selected_media = available_media[0]
    
    if not selected_media:
        print("✗ No media to select")
        return
    
    select_media_response = requests.post(
        f"{BASE_URL}/api/facebook/select_media",
        json={
            "media_id": selected_media.get("id"),
            "media_data": selected_media,
            "thread_id": thread_id
        }
    )
    
    if select_media_response.status_code == 200:
        print(f"✓ Media selected: {selected_media.get('filename')}")
    else:
        print(f"✗ Media selection failed: {select_media_response.status_code}")
        return
    
    # Step 5: Create Campaign with AI
    print("\n[Step 5] Creating campaign with AI agent...")
    create_response = requests.post(
        f"{BASE_URL}/api/facebook/campaign/create",
        json={"thread_id": thread_id}
    )
    
    if create_response.status_code == 200:
        create_data = create_response.json()
        campaign_config = create_data.get("campaign_config", {})
        print(f"✓ Campaign created!")
        print(f"  Campaign Name: {campaign_config.get('campaign', {}).get('name')}")
        print(f"  Objective: {campaign_config.get('campaign', {}).get('objective')}")
        print(f"  Daily Budget: ${campaign_config.get('adset', {}).get('daily_budget', 0) / 100}")
    else:
        print(f"✗ Campaign creation failed: {create_response.status_code}")
        return
    
    # Step 6: Generate Preview
    print("\n[Step 6] Generating campaign preview...")
    preview_response = requests.post(
        f"{BASE_URL}/api/facebook/campaign/preview",
        json={"thread_id": thread_id}
    )
    
    if preview_response.status_code == 200:
        preview_data = preview_response.json()
        campaign_preview = preview_data.get("campaign_preview", {})
        print(f"✓ Preview generated!")
        print("\n--- Campaign Preview ---")
        print(campaign_preview.get("preview_text", "No preview text available"))
        print("--- End Preview ---\n")
    else:
        print(f"✗ Preview generation failed: {preview_response.status_code}")
        return
    
    # Step 7: Modify Campaign
    print("\n[Step 7] Modifying campaign...")
    modify_response = requests.post(
        f"{BASE_URL}/api/facebook/campaign/modify",
        json={
            "modification_request": "Increase the daily budget to $50 and change the headline to be more engaging",
            "thread_id": thread_id
        }
    )
    
    if modify_response.status_code == 200:
        modify_data = modify_response.json()
        updated_config = modify_data.get("campaign_config", {})
        print(f"✓ Campaign modified!")
        print(f"  New Daily Budget: ${updated_config.get('adset', {}).get('daily_budget', 0) / 100}")
        print(f"  New Headline: {updated_config.get('ad', {}).get('headline')}")
    else:
        print(f"✗ Campaign modification failed: {modify_response.status_code}")
        return
    
    # Step 8: Publish Campaign (OPTIONAL - commented out for safety)
    print("\n[Step 8] Publishing campaign to Facebook...")
    print("⚠️  Publishing is disabled in test mode for safety")
    print("   To enable, uncomment the publish section in the test script")
    
    # Uncomment below to actually publish (USE WITH CAUTION!)
    """
    publish_response = requests.post(
        f"{BASE_URL}/api/facebook/campaign/publish",
        json={"thread_id": thread_id}
    )
    
    if publish_response.status_code == 200:
        publish_data = publish_response.json()
        print(f"✓ Campaign published!")
        print(f"  Campaign ID: {publish_data.get('campaign_id')}")
        print(f"  Ad Set ID: {publish_data.get('adset_id')}")
        print(f"  Ad ID: {publish_data.get('ad_id')}")
        print(f"  Campaign URL: {publish_data.get('campaign_url')}")
    else:
        print(f"✗ Campaign publishing failed: {publish_response.status_code}")
        return
    """
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
    print(f"\nThread ID: {thread_id}")
    print("You can use this thread_id to continue working with this campaign")


if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Before running this test:")
    print("1. Make sure the server is running (python server_langgraph.py)")
    print("2. Set FACEBOOK_ACCESS_TOKEN in your .env file")
    print("3. Ensure you have HeyGen-generated media in static/images or static/videos")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()
    
    try:
        test_facebook_campaign_flow()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to server. Is it running?")
        print("   Start the server with: python server_langgraph.py")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
