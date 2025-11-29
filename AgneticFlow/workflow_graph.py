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
            "generate_audio", "select_avatar", "generate_video"
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

