# LangGraph Architecture Summary

## Overview

The project has been refactored to use **LangGraph** for a state machine architecture that supports:
- ✅ Context-aware memory across all steps
- ✅ Bidirectional navigation (forward and backward)
- ✅ Chat-based editing at every step
- ✅ Agent integration for intelligent processing
- ✅ Image generation as an agent (not just API)

## File Structure

### Core LangGraph Files

1. **`state_schema.py`** - Defines the `WorkflowState` TypedDict
   - Complete state schema for the entire workflow
   - Tracks current step, navigation intent, messages, and all step-specific data

2. **`agents.py`** - Specialized LangChain agents
   - `AnalysisAgent`: Product analysis with refinement
   - `ScriptGenerationAgent`: Script generation and refinement
   - `ImageGenerationAgent`: Image prompt generation (agent-based)

3. **`workflow_graph.py`** - LangGraph state machine
   - `AdCampaignWorkflow`: Main workflow class
   - Nodes for each step (scrape, analyze, scripts, images, audio, video)
   - Routing logic for bidirectional navigation
   - Context preservation across steps

4. **`server_langgraph.py`** - FastAPI server with LangGraph integration
   - Workflow-based endpoints (`/api/workflow/*`)
   - Thread-based state management
   - Navigation and chat endpoints

### Updated Files

1. **`image_generation.py`** - Added `generate_ad_creatives_with_prompt()` method
   - Supports custom prompts from the ImageGenerationAgent

2. **`requirements.txt`** - Added dependencies
   - `langgraph` - For state machine
   - `google-genai` - For image generation
   - `pillow` - For image processing

## Workflow Steps

1. **SCRAPE** → Scrape product/store URL
2. **ANALYZE** → Analyze product (agent, editable via chat)
3. **GENERATE_SCRIPTS** → Generate 3 scripts (agent, editable via chat)
4. **SELECT_SCRIPT** → Select one script
5. **REFINE_SCRIPT** → Refine selected script (agent, editable via chat)
6. **GENERATE_IMAGES** → Generate images (agent, editable via chat)
7. **REFINE_IMAGES** → Refine images (agent, editable via chat)
8. **GENERATE_AUDIO** → Generate audio (Eleven Labs)
9. **SELECT_AVATAR** → Select HeyGen avatar
10. **GENERATE_VIDEO** → Generate lipsynced video

## Key Features

### 1. Context-Aware Memory
- All previous steps are remembered
- Selections persist across navigation
- Feedback history is maintained per step

### 2. Bidirectional Navigation
- Can go back to any previous step
- Can jump forward (if prerequisites met)
- Context is preserved when navigating

### 3. Chat-Based Editing
- Every step supports refinement via chat
- Messages are stored in state
- Agents use chat history for context

### 4. Agent Integration
- **AnalysisAgent**: Understands product context
- **ScriptGenerationAgent**: Creates engaging scripts
- **ImageGenerationAgent**: Generates detailed image prompts

## API Usage

### Starting Workflow

```python
# Scrape
POST /api/workflow/scrape
{
    "url": "https://example.com/product",
    "thread_id": null  # Auto-generated if null
}

# Analyze with feedback
POST /api/workflow/analyze
{
    "thread_id": "uuid",
    "feedback": "Focus on millennials"
}
```

### Navigation

```python
# Navigate to any step
POST /api/workflow/navigate
{
    "thread_id": "uuid",
    "navigation_intent": "go to analyze"
}

# Chat-based editing
POST /api/workflow/chat
{
    "thread_id": "uuid",
    "message": "Make it shorter"
}
```

## Migration Path

1. **Backend**: Use `server_langgraph.py` instead of `server.py`
2. **Frontend**: Update API calls to `/api/workflow/*` endpoints
3. **State Management**: Track `thread_id` per user session
4. **Navigation**: Use navigation endpoints for step changes

## Benefits

1. **Flexibility**: Users can refine any step at any time
2. **Context**: Full history available at every step
3. **Intelligence**: Agents understand context and user intent
4. **Scalability**: LangGraph handles complex state management
5. **Maintainability**: Clear separation of concerns

## Next Steps

1. Update frontend components to use new API
2. Add navigation UI (step indicators, back/forward buttons)
3. Implement chat interface for each step
4. Add state persistence (database) for production
5. Add error handling and validation
6. Add unit tests for workflow nodes

