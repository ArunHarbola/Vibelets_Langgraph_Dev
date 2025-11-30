"""
FastAPI server with LangGraph workflow integration
Supports context-aware, bidirectional navigation
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
from dotenv import load_dotenv
import uuid

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflow_graph import AdCampaignWorkflow
from state_schema import WorkflowState

load_dotenv()

app = FastAPI(title="Ad Campaign Generator API - LangGraph")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"Validation Error: {exc}")
    try:
        body = await request.json()
        print(f"Request Body: {body}")
    except:
        print("Could not read body")
        
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# Initialize workflow
workflow = AdCampaignWorkflow()

# Store active sessions (thread_id -> state)
active_sessions: Dict[str, WorkflowState] = {}

# --- Pydantic Models ---

class WorkflowRequest(BaseModel):
    """Base request for workflow operations"""
    thread_id: Optional[str] = None
    navigation_intent: Optional[str] = None  # e.g., "go to analyze", "go back to scripts"
    message: Optional[str] = None  # User message for chat-based editing

class ScrapeRequest(WorkflowRequest):
    url: str

class AnalyzeRequest(WorkflowRequest):
    feedback: Optional[str] = None

class ScriptRequest(WorkflowRequest):
    feedback: Optional[str] = None

class SelectScriptRequest(WorkflowRequest):
    script_index: int

class RefineScriptRequest(WorkflowRequest):
    feedback: str

class GenerateImagesRequest(WorkflowRequest):
    feedback: Optional[str] = None
    num_images: Optional[int] = 2

class RefineImagesRequest(WorkflowRequest):
    feedback: str

class GenerateAudioRequest(WorkflowRequest):
    pass

class SelectAvatarRequest(WorkflowRequest):
    avatar_id: str

class GenerateVideoRequest(WorkflowRequest):
    pass

class SelectProductRequest(WorkflowRequest):
    product_index: Optional[int] = None
    product_data: Optional[Dict[str, Any]] = None

# Facebook-specific request models
class FacebookAuthRequest(WorkflowRequest):
    access_token: str

class SelectAdAccountRequest(WorkflowRequest):
    account_id: str

class SelectMediaRequest(WorkflowRequest):
    media_id: str
    media_data: Dict[str, Any]

class CreateCampaignRequest(WorkflowRequest):
    pass

class ModifyCampaignRequest(WorkflowRequest):
    modification_request: str

class PublishCampaignRequest(WorkflowRequest):
    pass

# --- Helper Functions ---

def get_or_create_thread(thread_id: Optional[str] = None) -> str:
    """Get existing thread_id or create new one"""
    if not thread_id:
        thread_id = str(uuid.uuid4())
    
    if thread_id not in active_sessions:
        # Initialize new state
        active_sessions[thread_id] = {
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
            "iteration_count": {},
            # Facebook fields
            "facebook_access_token": None,
            "facebook_user_id": None,
            "facebook_ad_accounts": None,
            "selected_ad_account_id": None,
            "selected_ad_account": None,
            "available_media": None,
            "selected_media": None,
            "selected_media_type": None,
            "campaign_config": None,
            "campaign_preview": None,
            "campaign_modifications": [],
            "published_campaign_id": None,
            "published_adset_id": None,
            "published_ad_id": None,
            "campaign_status": None,
            "campaign_url": None
        }
    
    return thread_id

def update_state_from_request(state: WorkflowState, request: WorkflowRequest) -> WorkflowState:
    """Update state from request parameters"""
    if request.navigation_intent:
        state["navigation_intent"] = request.navigation_intent
        # Parse navigation intent to set current_step
        intent_lower = request.navigation_intent.lower()
        if "scrape" in intent_lower or "start" in intent_lower:
            state["current_step"] = "scrape"
        elif "analyze" in intent_lower or "analysis" in intent_lower:
            state["current_step"] = "analyze"
        elif "script" in intent_lower and "generate" in intent_lower:
            state["current_step"] = "generate_scripts"
        elif "script" in intent_lower and ("select" in intent_lower or "choose" in intent_lower):
            state["current_step"] = "select_script"
        elif "script" in intent_lower and ("refine" in intent_lower or "tweak" in intent_lower):
            state["current_step"] = "refine_script"
        elif "image" in intent_lower and "generate" in intent_lower:
            state["current_step"] = "generate_images"
        elif "image" in intent_lower and ("refine" in intent_lower or "edit" in intent_lower):
            state["current_step"] = "refine_images"
        elif "audio" in intent_lower:
            state["current_step"] = "generate_audio"
        elif "avatar" in intent_lower:
            state["current_step"] = "select_avatar"
        elif "video" in intent_lower:
            state["current_step"] = "generate_video"
    
    if request.message:
        # Add message to state for chat-based editing
        state["messages"].append({
            "role": "user",
            "content": request.message
        })
    
    return state

# --- Endpoints ---

@app.post("/api/workflow/scrape")
async def scrape_product(request: ScrapeRequest):
    """Scrape product/store URL"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Update state
    state["url"] = request.url
    state["current_step"] = "scrape"
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "current_step": result.get("current_step"),
        "product_data": result.get("product_data"),
        "error": result.get("error")
    }

@app.post("/api/workflow/analyze")
async def analyze_product(request: AnalyzeRequest):
    """Analyze product with optional feedback"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Update state
    state["current_step"] = "analyze"
    if request.feedback:
        state["analysis_feedback"].append(request.feedback)
        state["messages"].append({
            "role": "user",
            "content": request.feedback
        })
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    print(f"Calling workflow.run_step for thread {thread_id}")
    result = await workflow.run_step(state, config)
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "current_step": result.get("current_step"),
        "analysis": result.get("analysis"),
        "error": result.get("error")
    }

@app.post("/api/workflow/generate_scripts")
async def generate_scripts(request: ScriptRequest):
    """Generate ad scripts with optional feedback"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Update state
    state["current_step"] = "generate_scripts"
    if request.feedback:
        state["script_feedback"].append(request.feedback)
        state["messages"].append({
            "role": "user",
            "content": request.feedback
        })
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "current_step": result.get("current_step"),
        "scripts": result.get("scripts"),
        "error": result.get("error")
    }

@app.post("/api/workflow/select_script")
async def select_script(request: SelectScriptRequest):
    """Select a script by index"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Update state
    state["current_step"] = "select_script"
    state["selected_script_index"] = request.script_index
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "current_step": result.get("current_step"),
        "selected_script": result.get("selected_script"),
        "error": result.get("error")
    }

@app.post("/api/workflow/refine_script")
async def refine_script(request: RefineScriptRequest):
    """Refine selected script with feedback"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Update state
    state["current_step"] = "refine_script"
    state["messages"].append({
        "role": "user",
        "content": request.feedback
    })
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "current_step": result.get("current_step"),
        "selected_script": result.get("selected_script"),
        "error": result.get("error")
    }

@app.post("/api/workflow/generate_images")
async def generate_images(request: GenerateImagesRequest):
    """Generate images with optional feedback"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Update state
    state["current_step"] = "generate_images"
    if request.feedback:
        state["image_feedback"].append(request.feedback)
        state["messages"].append({
            "role": "user",
            "content": request.feedback
        })
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "current_step": result.get("current_step"),
        "generated_images": result.get("generated_images"),
        "image_generation_prompt": result.get("image_generation_prompt"),
        "error": result.get("error")
    }

@app.post("/api/workflow/refine_images")
async def refine_images(request: RefineImagesRequest):
    """Refine images with feedback"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Update state
    state["current_step"] = "refine_images"
    state["image_feedback"].append(request.feedback)
    state["messages"].append({
        "role": "user",
        "content": request.feedback
    })
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "current_step": result.get("current_step"),
        "generated_images": result.get("generated_images"),
        "image_generation_prompt": result.get("image_generation_prompt"),
        "error": result.get("error")
    }

@app.post("/api/workflow/generate_audio")
async def generate_audio(request: GenerateAudioRequest):
    """Generate audio from selected script"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Update state
    state["current_step"] = "generate_audio"
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "current_step": result.get("current_step"),
        "audio_file": result.get("audio_file"),
        "audio_url": result.get("audio_url"),
        "error": result.get("error")
    }

@app.post("/api/workflow/select_avatar")
async def select_avatar(request: SelectAvatarRequest):
    """Select HeyGen avatar"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Update state
    state["current_step"] = "select_avatar"
    state["selected_avatar_id"] = request.avatar_id
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "current_step": result.get("current_step"),
        "available_avatars": result.get("available_avatars"),
        "selected_avatar_id": result.get("selected_avatar_id"),
        "error": result.get("error")
    }

@app.get("/api/workflow/avatars")
async def get_avatars(thread_id: Optional[str] = None):
    """Get available avatars"""
    thread_id = get_or_create_thread(thread_id)
    state = active_sessions[thread_id]
    
    # If avatars not loaded, load them
    if not state.get("available_avatars"):
        from heygen import HeyGenAvatarIntegrator
        heygen = HeyGenAvatarIntegrator()
        avatars = heygen.get_avatars()
        state["available_avatars"] = avatars
        active_sessions[thread_id] = state
    
    return {
        "thread_id": thread_id,
        "avatars": state.get("available_avatars", [])
    }

@app.post("/api/workflow/generate_video")
async def generate_video(request: GenerateVideoRequest):
    """Generate HeyGen video"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Update state
    state["current_step"] = "generate_video"
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "current_step": result.get("current_step"),
        "video_id": result.get("video_id"),
        "video_url": result.get("video_url"),
        "video_status": result.get("video_status"),
        "error": result.get("error")
    }

@app.get("/api/workflow/state/{thread_id}")
async def get_state(thread_id: str):
    """Get current workflow state"""
    if thread_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    return {
        "thread_id": thread_id,
        "state": active_sessions[thread_id]
    }

@app.post("/api/workflow/navigate")
async def navigate(request: WorkflowRequest):
    """Navigate to any step in the workflow"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Update navigation intent
    state = update_state_from_request(state, request)
    
    # Run workflow step (will route to appropriate node)
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "current_step": result.get("current_step"),
        "error": result.get("error")
    }

@app.post("/api/workflow/chat")
async def chat(request: WorkflowRequest):
    """Chat-based editing - automatically routes to current step with message"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    if not request.message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Add message to state
    state["messages"].append({
        "role": "user",
        "content": request.message
    })
    
    # Determine which step to route to based on current step
    current_step = state.get("current_step", "scrape")
    
    # If navigation intent provided, use it
    if request.navigation_intent:
        state = update_state_from_request(state, request)
        current_step = state.get("current_step")
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "current_step": result.get("current_step"),
        "error": result.get("error")
    }

# ===== Facebook Campaign Endpoints =====

@app.post("/api/facebook/authenticate")
async def facebook_authenticate(request: FacebookAuthRequest):
    """Authenticate with Facebook and get ad accounts"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Set access token
    state["facebook_access_token"] = request.access_token
    state["current_step"] = "authenticate_facebook"
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "user_id": result.get("facebook_user_id"),
        "ad_accounts": result.get("facebook_ad_accounts"),
        "error": result.get("error")
    }

@app.post("/api/facebook/select_account")
async def select_facebook_account(request: SelectAdAccountRequest):
    """Select Facebook ad account"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Set selected account
    state["selected_ad_account_id"] = request.account_id
    state["current_step"] = "select_ad_account"
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "selected_account": result.get("selected_ad_account"),
        "error": result.get("error")
    }

@app.get("/api/facebook/media")
async def list_facebook_media(thread_id: Optional[str] = None):
    """List available media (HeyGen-generated images and videos)"""
    thread_id = get_or_create_thread(thread_id)
    state = active_sessions[thread_id]
    
    # Set current step
    state["current_step"] = "list_media"
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "available_media": result.get("available_media", []),
        "error": result.get("error")
    }

@app.post("/api/facebook/select_media")
async def select_facebook_media(request: SelectMediaRequest):
    """Select media for campaign"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Set selected media
    state["selected_media"] = request.media_data
    state["current_step"] = "select_media"
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "selected_media": result.get("selected_media"),
        "error": result.get("error")
    }

@app.post("/api/facebook/campaign/create")
async def create_facebook_campaign(request: CreateCampaignRequest):
    """Create campaign configuration using AI"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Set current step
    state["current_step"] = "create_campaign"
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "campaign_config": result.get("campaign_config"),
        "campaign_status": result.get("campaign_status"),
        "error": result.get("error")
    }

@app.post("/api/facebook/campaign/preview")
async def preview_facebook_campaign(request: WorkflowRequest):
    """Generate campaign preview"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Set current step
    state["current_step"] = "preview_campaign"
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "campaign_preview": result.get("campaign_preview"),
        "campaign_config": result.get("campaign_config"),
        "error": result.get("error")
    }

@app.post("/api/facebook/campaign/modify")
async def modify_facebook_campaign(request: ModifyCampaignRequest):
    """Modify campaign based on user feedback"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Add modification request as message
    state["messages"].append({
        "role": "user",
        "content": request.modification_request
    })
    state["current_step"] = "modify_campaign"
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "campaign_config": result.get("campaign_config"),
        "campaign_preview": result.get("campaign_preview"),
        "error": result.get("error")
    }

@app.post("/api/facebook/campaign/publish")
async def publish_facebook_campaign(request: PublishCampaignRequest):
    """Publish campaign to Facebook Ads"""
    thread_id = get_or_create_thread(request.thread_id)
    state = active_sessions[thread_id]
    
    # Set current step
    state["current_step"] = "publish_campaign"
    state = update_state_from_request(state, request)
    
    # Run workflow step
    config = {"configurable": {"thread_id": thread_id}}
    result = await workflow.run_step(state, config)
    
    # Update session
    active_sessions[thread_id] = result
    
    return {
        "thread_id": thread_id,
        "state": result,
        "campaign_id": result.get("published_campaign_id"),
        "adset_id": result.get("published_adset_id"),
        "ad_id": result.get("published_ad_id"),
        "campaign_url": result.get("campaign_url"),
        "campaign_status": result.get("campaign_status"),
        "error": result.get("error")
    }

# Mount static files
from fastapi.staticfiles import StaticFiles
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

