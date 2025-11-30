"""
Not in used
This file contains in Workflow graph.
Facebook Campaign Workflow Nodes
Additional nodes for the AdCampaignWorkflow class
These should be added to workflow_graph.py
"""

# Add these methods to the AdCampaignWorkflow class in workflow_graph.py

async def _authenticate_facebook_node(self, state):
    """Authenticate user with Facebook"""
    from facebook.auth import authenticate_user
    
    state["current_step"] = "authenticate_facebook"
    
    access_token = state.get("facebook_access_token")
    if not access_token:
        state["error"] = "No Facebook access token provided"
        return state
    
    # Authenticate and get user info + ad accounts
    auth_result = await authenticate_user(access_token)
    
    if not auth_result.get("success"):
        state["error"] = auth_result.get("error", "Authentication failed")
        return state
    
    state["facebook_user_id"] = auth_result["user_id"]
    state["facebook_ad_accounts"] = auth_result["ad_accounts"]
    
    return state

def _select_ad_account_node(self, state):
    """Select Facebook ad account"""
    state["current_step"] = "select_ad_account"
    
    account_id = state.get("selected_ad_account_id")
    ad_accounts = state.get("facebook_ad_accounts", [])
    
    if not account_id:
        state["error"] = "No ad account selected"
        return state
    
    # Find the selected account
    selected_account = None
    for account in ad_accounts:
        if account.get("id") == f"act_{account_id}" or account.get("id") == account_id:
            selected_account = account
            break
    
    if not selected_account:
        state["error"] = f"Ad account {account_id} not found"
        return state
    
    state["selected_ad_account"] = selected_account
    
    return state

def _list_media_node(self, state):
    """List available media (HeyGen-generated images and videos)"""
    state["current_step"] = "list_media"
    
    # Get all available media
    all_media = self.media_manager.list_all_media()
    
    # Combine images and videos into a single list
    media_list = []
    for image in all_media["images"]:
        media_list.append(image)
    for video in all_media["videos"]:
        media_list.append(video)
    
    state["available_media"] = media_list
    
    return state

def _select_media_node(self, state):
    """Select media for campaign"""
    state["current_step"] = "select_media"
    
    selected_media = state.get("selected_media")
    
    if not selected_media:
        state["error"] = "No media selected"
        return state
    
    # Validate media exists
    media_id = selected_media.get("id")
    media = self.media_manager.get_media_by_id(media_id)
    
    if not media:
        state["error"] = f"Media {media_id} not found"
        return state
    
    state["selected_media"] = media
    state["selected_media_type"] = media.get("type")
    
    return state

async def _create_campaign_node(self, state):
    """Create campaign configuration using AI agent"""
    state["current_step"] = "create_campaign"
    
    selected_media = state.get("selected_media")
    
    if not selected_media:
        state["error"] = "No media selected. Please select media first."
        return state
    
    # Build context from product analysis and script if available
    context_parts = []
    
    if state.get("analysis"):
        context_parts.append(f"Product Analysis: {state['analysis']}")
    
    if state.get("selected_script"):
        context_parts.append(f"Ad Script: {state['selected_script']}")
    
    context = "\n\n".join(context_parts) if context_parts else None
    
    # Generate campaign configuration
    campaign_config = await self.campaign_creation_agent.create_campaign(
        selected_media,
        context
    )
    
    state["campaign_config"] = campaign_config
    state["campaign_status"] = "draft"
    
    return state

async def _preview_campaign_node(self, state):
    """Generate campaign preview"""
    state["current_step"] = "preview_campaign"
    
    campaign_config = state.get("campaign_config")
    selected_media = state.get("selected_media")
    
    if not campaign_config:
        state["error"] = "No campaign configuration. Please create campaign first."
        return state
    
    if not selected_media:
        state["error"] = "No media selected."
        return state
    
    # Generate preview
    preview = await self.campaign_preview_agent.generate_preview(
        campaign_config,
        selected_media
    )
    
    state["campaign_preview"] = preview
    state["campaign_status"] = "preview"
    
    return state

async def _modify_campaign_node(self, state):
    """Modify campaign based on user feedback"""
    state["current_step"] = "modify_campaign"
    
    campaign_config = state.get("campaign_config")
    messages = state.get("messages", [])
    
    if not campaign_config:
        state["error"] = "No campaign configuration to modify."
        return state
    
    # Get latest user message as modification request
    if not messages:
        state["error"] = "No modification request provided."
        return state
    
    latest_message = messages[-1]
    if latest_message.get("role") != "user":
        state["error"] = "No user modification request found."
        return state
    
    modification_request = latest_message.get("content")
    
    # Apply modifications
    updated_config = await self.campaign_modification_agent.modify_campaign(
        campaign_config,
        modification_request
    )
    
    state["campaign_config"] = updated_config
    
    # Track modification
    if "campaign_modifications" not in state:
        state["campaign_modifications"] = []
    state["campaign_modifications"].append(modification_request)
    
    # Regenerate preview
    preview = await self.campaign_preview_agent.generate_preview(
        updated_config,
        state.get("selected_media")
    )
    state["campaign_preview"] = preview
    state["campaign_status"] = "modified"
    
    return state

async def _publish_campaign_node(self, state):
    """Publish campaign to Facebook Ads"""
    from facebook.campaigns import create_campaign
    from facebook.adsets import create_adset
    from facebook.ads import create_video_ad
    from facebook.media import upload_media_service
    from datetime import datetime, timedelta
    
    state["current_step"] = "publish_campaign"
    state["campaign_status"] = "publishing"
    
    campaign_config = state.get("campaign_config")
    selected_media = state.get("selected_media")
    access_token = state.get("facebook_access_token")
    account_id = state.get("selected_ad_account_id")
    
    if not all([campaign_config, selected_media, access_token, account_id]):
        state["error"] = "Missing required data for publishing"
        return state
    
    try:
        # Step 1: Create Campaign
        campaign_data = campaign_config.get("campaign", {})
        campaign_result = await create_campaign(
            account_id=account_id,
            name=campaign_data.get("name", "AI Generated Campaign"),
            objective=campaign_data.get("objective", "OUTCOME_TRAFFIC"),
            access_token=access_token,
            special_ad_categories=campaign_data.get("special_ad_categories", ["NONE"])
        )
        
        campaign_id = campaign_result.get("id")
        state["published_campaign_id"] = campaign_id
        
        # Step 2: Upload Media
        media_type = "video" if selected_media.get("type") == "video" else "image"
        media_result = upload_media_service(
            account_id=account_id,
            media_type=media_type,
            access_token=access_token,
            temp_path=selected_media.get("file_path")
        )
        
        if "error" in media_result:
            state["error"] = f"Media upload failed: {media_result['error']}"
            return state
        
        media_hash = media_result.get("hash")
        video_id = media_result.get("video_id") if media_type == "video" else None
        
        # Step 3: Create Ad Set
        adset_data = campaign_config.get("adset", {})
        
        # Calculate start and end times
        start_time = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S%z")
        end_time = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S%z")
        
        adset_result = await create_adset(
            account_id=account_id,
            campaign_id=campaign_id,
            name=adset_data.get("name", "AI Generated Ad Set"),
            daily_budget=adset_data.get("daily_budget", 2000),
            start_time=start_time,
            end_time=end_time,
            access_token=access_token,
            targeting=adset_data.get("targeting")
        )
        
        adset_id = adset_result.get("id")
        state["published_adset_id"] = adset_id
        
        # Step 4: Create Ad
        ad_data = campaign_config.get("ad", {})
        
        # Get page_id from selected ad account (use first page or default)
        page_id = state.get("selected_ad_account", {}).get("page_id", "YOUR_PAGE_ID")
        
        if media_type == "video":
            ad_result = await create_video_ad(
                account_id=account_id,
                adset_id=adset_id,
                page_id=page_id,
                ad_name=ad_data.get("name", "AI Generated Ad"),
                video_id=video_id,
                thumbnail_hash=media_hash,
                message=ad_data.get("primary_text", ""),
                link=ad_data.get("link", "https://example.com"),
                access_token=access_token
            )
        else:
            # For image ads, we'd use a different function (not implemented yet)
            # For now, use video ad function with image hash
            ad_result = await create_video_ad(
                account_id=account_id,
                adset_id=adset_id,
                page_id=page_id,
                ad_name=ad_data.get("name", "AI Generated Ad"),
                video_id=None,
                thumbnail_hash=media_hash,
                message=ad_data.get("primary_text", ""),
                link=ad_data.get("link", "https://example.com"),
                access_token=access_token
            )
        
        ad_id = ad_result.get("id")
        state["published_ad_id"] = ad_id
        
        # Generate campaign URL
        state["campaign_url"] = f"https://business.facebook.com/adsmanager/manage/campaigns?act={account_id}&selected_campaign_ids={campaign_id}"
        state["campaign_status"] = "published"
        
    except Exception as e:
        state["error"] = f"Publishing failed: {str(e)}"
        state["campaign_status"] = "draft"
    
    return state
