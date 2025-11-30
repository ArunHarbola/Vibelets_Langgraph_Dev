"""
LangGraph workflow for ad campaign generation
Supports bidirectional navigation and context-aware memory
"""
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state_schema import WorkflowState
from scraper import ProductScraper
from agents import AnalysisAgent, ScriptGenerationAgent, ImageGenerationAgent, NavigationAgent
from audioGeneration import ElevenLabsVoiceGenerator
from heygen import HeyGenAvatarIntegrator
from facebook_agents import CampaignCreationAgent, CampaignPreviewAgent, CampaignModificationAgent
from media_manager import MediaManager
import os


class AdCampaignWorkflow:
    """LangGraph-based workflow with bidirectional navigation"""
    
    def __init__(self):
        self.scraper = ProductScraper()
        self.analysis_agent = AnalysisAgent()
        self.script_agent = ScriptGenerationAgent()
        self.image_agent = ImageGenerationAgent()
        self.audio_gen = ElevenLabsVoiceGenerator()
        self.heygen = HeyGenAvatarIntegrator()
        self.navigation_agent = NavigationAgent()
        
        # Facebook campaign agents
        self.campaign_creation_agent = CampaignCreationAgent()
        self.campaign_preview_agent = CampaignPreviewAgent()
        self.campaign_modification_agent = CampaignModificationAgent()
        self.media_manager = MediaManager()
        
        # Build the graph
        self.graph = self._build_graph()
        
        # Add memory for checkpointing
        self.memory = MemorySaver()
        self.app = self.graph.compile(checkpointer=self.memory)
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each step
        workflow.add_node("scrape", self._scrape_node)
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("generate_scripts", self._generate_scripts_node)
        workflow.add_node("select_script", self._select_script_node)
        workflow.add_node("refine_script", self._refine_script_node)
        workflow.add_node("generate_images", self._generate_images_node)
        workflow.add_node("refine_images", self._refine_images_node)
        workflow.add_node("generate_audio", self._generate_audio_node)
        workflow.add_node("select_avatar", self._select_avatar_node)
        workflow.add_node("generate_video", self._generate_video_node)
        
        # Facebook campaign nodes
        workflow.add_node("authenticate_facebook", self._authenticate_facebook_node)
        workflow.add_node("select_ad_account", self._select_ad_account_node)
        workflow.add_node("list_media", self._list_media_node)
        workflow.add_node("select_media", self._select_media_node)
        workflow.add_node("create_campaign", self._create_campaign_node)
        workflow.add_node("preview_campaign", self._preview_campaign_node)
        workflow.add_node("modify_campaign", self._modify_campaign_node)
        workflow.add_node("publish_campaign", self._publish_campaign_node)
        
        workflow.add_node("route", self._route_node)
        
        # Set entry point
        workflow.set_entry_point("route")
        
        # Define edges - all nodes route to END to wait for next interaction
        workflow.add_edge("scrape", END)
        workflow.add_edge("analyze", END)
        workflow.add_edge("generate_scripts", END)
        workflow.add_edge("select_script", END)
        workflow.add_edge("refine_script", END)
        workflow.add_edge("generate_images", END)
        workflow.add_edge("refine_images", END)
        workflow.add_edge("generate_audio", END)
        workflow.add_edge("select_avatar", END)
        workflow.add_edge("generate_video", END)
        
        # Facebook campaign edges
        workflow.add_edge("authenticate_facebook", END)
        workflow.add_edge("select_ad_account", END)
        workflow.add_edge("list_media", END)
        workflow.add_edge("select_media", END)
        workflow.add_edge("create_campaign", END)
        workflow.add_edge("preview_campaign", END)
        workflow.add_edge("modify_campaign", END)
        workflow.add_edge("publish_campaign", END)
        
        # Route node conditionally routes to next step or END
        workflow.add_conditional_edges(
            "route",
            self._route_logic,
            {
                "scrape": "scrape",
                "analyze": "analyze",
                "generate_scripts": "generate_scripts",
                "select_script": "select_script",
                "refine_script": "refine_script",
                "generate_images": "generate_images",
                "refine_images": "refine_images",
                "generate_audio": "generate_audio",
                "select_avatar": "select_avatar",
                "generate_video": "generate_video",
                "authenticate_facebook": "authenticate_facebook",
                "select_ad_account": "select_ad_account",
                "list_media": "list_media",
                "select_media": "select_media",
                "create_campaign": "create_campaign",
                "preview_campaign": "preview_campaign",
                "modify_campaign": "modify_campaign",
                "publish_campaign": "publish_campaign",
                END: END
            }
        )
        
        return workflow
    
    async def _route_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Entry point node that determines navigation"""
        # Analyze intent using agent
        result = await self.navigation_agent.analyze_intent(state)
        intent = result.get("intent")
        
        print(f"Navigation Intent: {intent} (Reason: {result.get('reasoning')})")
        
        # Map 'next' to the actual next step based on current_step
        if intent == "next":
            current = state.get("current_step")
            if current == "scrape":
                intent = "analyze"
            elif current == "analyze":
                intent = "generate_scripts"
            elif current == "generate_scripts":
                intent = "select_script"
            elif current == "select_script":
                intent = "refine_script"
            elif current == "refine_script":
                intent = "generate_images"
            elif current == "generate_images":
                intent = "refine_images"
            elif current == "refine_images":
                intent = "generate_audio"
            elif current == "generate_audio":
                intent = "select_avatar"
            elif current == "select_avatar":
                intent = "generate_video"
            elif current == "generate_video":
                intent = "complete"
        
        # Map 'stay' to current step
        elif intent == "stay":
            intent = state.get("current_step")
            
        return {"navigation_intent": intent}

    def _route_logic(self, state: WorkflowState) -> str:
        """Route to the appropriate step based on navigation_intent."""
        intent = state.get("navigation_intent")
        current_step = state.get("current_step", "scrape")
        
        # If intent is a valid step name, go there
        valid_steps = [
            "scrape", "analyze", "generate_scripts", "select_script", 
            "refine_script", "generate_images", "refine_images", 
            "generate_audio", "select_avatar", "generate_video",
            "authenticate_facebook", "select_ad_account", "list_media",
            "select_media", "create_campaign", "preview_campaign",
            "modify_campaign", "publish_campaign"
        ]
        
        if intent in valid_steps:
            return intent
        elif intent == "complete":
            return END
            
        # Fallback to current step or END
        return current_step if current_step in valid_steps else END
    
    def _scrape_node(self, state: WorkflowState) -> WorkflowState:
        """Scrape product/store URL"""
        # Update current_step in state
        state["current_step"] = "scrape"
        
        url = state.get("url")
        if not url:
            state["error"] = "No URL provided"
            return state
        
        # Check if we already have product data (if navigating back)
        if state.get("product_data") and state.get("url") == url:
            # Already scraped, return existing data
            return state
        
        product_data = self.scraper.scrape_url(url)
        
        if "error" in product_data:
            state["error"] = product_data["error"]
            return state
        
        state["product_data"] = product_data
        state["selected_product"] = product_data  # Default to the scraped product
        
        # Handle store selection if needed
        if product_data.get("is_store") and product_data.get("products"):
            # For now, use first product or let frontend handle selection
            # Frontend can update selected_product via API
            pass
        
        # Update iteration count
        if "iteration_count" not in state:
            state["iteration_count"] = {}
        state["iteration_count"]["scrape"] = state["iteration_count"].get("scrape", 0) + 1
        
        return state
    
    async def _analyze_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze product using agent"""
        # Update current_step in state
        state["current_step"] = "analyze"
        
        product_data = state.get("selected_product") or state.get("product_data")
        if not product_data:
            state["error"] = "No product data available. Please scrape first."
            return state
        
        # Get feedback history
        feedback_history = state.get("analysis_feedback", [])
        
        # Check if user provided new feedback in messages
        messages = state.get("messages", [])
        if messages:
            latest_message = messages[-1]
            if latest_message.get("role") == "user" and latest_message.get("content"):
                feedback_history.append(latest_message["content"])
                state["analysis_feedback"] = feedback_history
        
        # Prepare product data with current analysis for refinement
        if state.get("analysis"):
            product_data["current_analysis"] = state["analysis"]
        
        # Generate or refine analysis
        analysis = await self.analysis_agent.analyze(product_data, feedback_history)
        state["analysis"] = analysis
        
        # Update iteration count
        if "iteration_count" not in state:
            state["iteration_count"] = {}
        state["iteration_count"]["analyze"] = state["iteration_count"].get("analyze", 0) + 1
        
        return state
    
    async def _generate_scripts_node(self, state: WorkflowState) -> WorkflowState:
        """Generate ad scripts using agent"""
        # Update current_step in state
        state["current_step"] = "generate_scripts"
        
        product_data = state.get("selected_product") or state.get("product_data")
        analysis = state.get("analysis")
        
        if not product_data:
            state["error"] = "No product data available. Please scrape first."
            return state
        
        if not analysis:
            state["error"] = "No analysis available. Please analyze product first."
            return state
        
        # Get feedback history
        feedback_history = state.get("script_feedback", [])
        
        # Check if user provided new feedback in messages
        messages = state.get("messages", [])
        if messages:
            latest_message = messages[-1]
            if latest_message.get("role") == "user" and latest_message.get("content"):
                feedback_history.append(latest_message["content"])
                state["script_feedback"] = feedback_history
        
        # Prepare for refinement if scripts already exist
        if state.get("scripts"):
            product_data["current_scripts"] = state["scripts"]
        
        # Generate or refine scripts
        scripts = await self.script_agent.generate_scripts(product_data, analysis, feedback_history)
        state["scripts"] = scripts
        
        # Update iteration count
        if "iteration_count" not in state:
            state["iteration_count"] = {}
        state["iteration_count"]["generate_scripts"] = state["iteration_count"].get("generate_scripts", 0) + 1
        
        return state
    
    def _select_script_node(self, state: WorkflowState) -> WorkflowState:
        """Select a script (handled by frontend, this node just validates)"""
        # Update current_step in state
        state["current_step"] = "select_script"
        
        scripts = state.get("scripts")
        script_index = state.get("selected_script_index")
        
        if not scripts:
            state["error"] = "No scripts available. Please generate scripts first."
            return state
        
        if script_index is None or script_index < 0 or script_index >= len(scripts):
            state["error"] = f"Invalid script index. Please select 0-{len(scripts)-1}"
            return state
        
        state["selected_script"] = scripts[script_index]
        return state
    
    async def _refine_script_node(self, state: WorkflowState) -> WorkflowState:
        """Refine selected script using agent"""
        # Update current_step in state
        state["current_step"] = "refine_script"
        
        selected_script = state.get("selected_script")
        if not selected_script:
            state["error"] = "No script selected. Please select a script first."
            return state
        
        # Get feedback from messages
        messages = state.get("messages", [])
        if messages:
            latest_message = messages[-1]
            if latest_message.get("role") == "user" and latest_message.get("content"):
                feedback = latest_message["content"]
                refined = await self.script_agent.refine_script(selected_script, feedback)
                state["selected_script"] = refined
                if "script_refinement_feedback" not in state:
                    state["script_refinement_feedback"] = []
                state["script_refinement_feedback"].append(feedback)
        
        # Update iteration count
        if "iteration_count" not in state:
            state["iteration_count"] = {}
        state["iteration_count"]["refine_script"] = state["iteration_count"].get("refine_script", 0) + 1
        
        return state
    
    async def _generate_images_node(self, state: WorkflowState) -> WorkflowState:
        """Generate images using agent"""
        # Update current_step in state
        state["current_step"] = "generate_images"
        
        product_data = state.get("selected_product") or state.get("product_data")
        selected_script = state.get("selected_script")
        analysis = state.get("analysis")
        
        if not product_data or not product_data.get("url"):
            state["error"] = "No product URL available. Please scrape first."
            return state
        
        if not selected_script:
            state["error"] = "No script selected. Please select a script first."
            return state
        
        # Generate or refine image prompt
        image_feedback = state.get("image_feedback", [])
        current_prompt = state.get("image_generation_prompt")
        
        # Check if user provided new feedback in messages
        messages = state.get("messages", [])
        feedback = None
        if messages:
            latest_message = messages[-1]
            if latest_message.get("role") == "user" and latest_message.get("content"):
                feedback = latest_message["content"]
                image_feedback.append(feedback)
                state["image_feedback"] = image_feedback
        
        # Generate prompt using agent
        image_prompt = await self.image_agent.generate_prompt(
            product_data,
            selected_script,
            analysis,
            feedback if feedback else None
        )
        state["image_generation_prompt"] = image_prompt
        
        # Generate images
        product_url = product_data.get("url")
        # Note: image_gen.generate_images is still synchronous as it uses Selenium/requests
        # We might need to wrap it in run_in_executor if it blocks too long, but for now let's keep it sync
        # as it's not an LLM call causing the specific error we're fixing.
        # However, if we wanted to be fully async:
        # import asyncio
        # loop = asyncio.get_running_loop()
        # images = await loop.run_in_executor(None, self.image_agent.generate_images, product_url, image_prompt, 2)
        
        images = self.image_agent.generate_images(product_url, image_prompt, num_images=2)
        state["generated_images"] = images
        
        # Update iteration count
        if "iteration_count" not in state:
            state["iteration_count"] = {}
        state["iteration_count"]["generate_images"] = state["iteration_count"].get("generate_images", 0) + 1
        
        return state
    
    async def _refine_images_node(self, state: WorkflowState) -> WorkflowState:
        """Refine images (regenerate with new prompt)"""
        # Update current_step in state
        state["current_step"] = "refine_images"
        # This is essentially the same as generate_images but with explicit feedback
        return await self._generate_images_node(state)
    
    def _generate_audio_node(self, state: WorkflowState) -> WorkflowState:
        """Generate audio using Eleven Labs"""
        # Update current_step in state
        state["current_step"] = "generate_audio"
        
        selected_script = state.get("selected_script")
        if not selected_script:
            state["error"] = "No script selected. Please select a script first."
            return state
        
        # Check if audio already exists (if navigating back)
        if state.get("audio_file") and os.path.exists(state["audio_file"]):
            return state
        
        # Generate audio
        os.makedirs("static/audio", exist_ok=True)
        filename = f"static/audio/generated_audio_{state.get('iteration_count', {}).get('generate_audio', 0)}.mp3"
        audio_file = self.audio_gen.generate_voice(selected_script, filename)
        
        if audio_file:
            state["audio_file"] = audio_file
            state["audio_url"] = f"/static/audio/{os.path.basename(audio_file)}"
        else:
            state["error"] = "Audio generation failed"
        
        # Update iteration count
        if "iteration_count" not in state:
            state["iteration_count"] = {}
        state["iteration_count"]["generate_audio"] = state["iteration_count"].get("generate_audio", 0) + 1
        
        return state
    
    def _select_avatar_node(self, state: WorkflowState) -> WorkflowState:
        """Select HeyGen avatar"""
        # Update current_step in state
        state["current_step"] = "select_avatar"
        
        # Fetch avatars if not already fetched
        if not state.get("available_avatars"):
            avatars = self.heygen.get_avatars()
            state["available_avatars"] = avatars
        
        # Avatar selection is handled by frontend
        # This node just validates that an avatar is selected
        avatar_id = state.get("selected_avatar_id")
        if not avatar_id:
            # Default to first avatar if none selected
            avatars = state.get("available_avatars", [])
            if avatars:
                state["selected_avatar_id"] = avatars[0].get("avatar_id")
        
        return state
    
    def _generate_video_node(self, state: WorkflowState) -> WorkflowState:
        """Generate HeyGen video"""
        # Update current_step in state
        state["current_step"] = "generate_video"
        
        audio_file = state.get("audio_file")
        avatar_id = state.get("selected_avatar_id")
        
        if not audio_file:
            state["error"] = "No audio file available. Please generate audio first."
            return state
        
        if not avatar_id:
            state["error"] = "No avatar selected. Please select an avatar first."
            return state
        
        # Upload audio to HeyGen if not already uploaded
        # For now, we'll assume the audio needs to be uploaded each time
        # In production, you might want to cache the asset_id
        asset_id = self.heygen.upload_asset(audio_file)
        
        if not asset_id:
            state["error"] = "Failed to upload audio to HeyGen"
            return state
        
        # Create video
        result = self.heygen.create_avatar_video(asset_id, avatar_id=avatar_id, is_asset_id=True)
        
        if "error" in result:
            state["error"] = result["error"]
            return state
        
        video_id = result.get("video_id")
        state["video_id"] = video_id
        
        # Check status
        status = self.heygen.check_video_status(video_id)
        state["video_status"] = status.get("status", "processing")
        state["video_url"] = status.get("video_url")
        
        # Update iteration count
        if "iteration_count" not in state:
            state["iteration_count"] = {}
        state["iteration_count"]["generate_video"] = state["iteration_count"].get("generate_video", 0) + 1
        
        return state
    
    # ===== Facebook Campaign Nodes =====
    
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

        async def run_step(self, state: WorkflowState, config: Dict = None) -> WorkflowState:
        """Execute one step of the workflow"""
        if config is None:
            config = {"configurable": {"thread_id": "default"}}
        
        # Run the graph
        result = await self.app.ainvoke(state, config)
        return result
    
    def get_state(self, thread_id: str = "default") -> WorkflowState:
        """Get current state for a thread"""
        config = {"configurable": {"thread_id": thread_id}}
        # Get the latest state from memory
        # This is a simplified version - in production you'd use get_state_stream
        # For now, return empty state - server maintains state
        return {
            "current_step": "scrape",
            "navigation_intent": None,
            "messages": [],
            "url": None,
            "product_data": None,
            "selected_product": None,
            "analysis": None,
            "analysis_feedback": [],
            "scripts": None,
            "script_feedback": [],
            "selected_script_index": None,
            "selected_script": None,
            "script_refinement_feedback": [],
            "generated_images": None,
            "image_feedback": [],
            "image_generation_prompt": None,
            "audio_file": None,
            "audio_url": None,
            "available_avatars": None,
            "selected_avatar_id": None,
            "video_id": None,
            "video_url": None,
            "video_status": None,
            "error": None,
            "iteration_count": {}
        }

