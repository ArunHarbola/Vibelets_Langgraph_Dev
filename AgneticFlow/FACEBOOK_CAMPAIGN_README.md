# Facebook Ad Campaign AgentFlow

Complete LangGraph-based workflow for creating Facebook ad campaigns using HeyGen-generated media and AI agents.

## Quick Start

### 1. Prerequisites
- Python 3.8+
- Facebook Developer Account with access token
- HeyGen-generated media (images/videos) in `static/images` or `static/videos`

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables
Create or update `.env`:
```
GOOGLE_API_KEY=your_google_api_key
META_ACCESS_TOKEN=your_facebook_access_token
HEYGEN_API_KEY=your_heygen_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

### 4. Start the Server
```bash
cd AgneticFlow
python server_langgraph.py
```

Server will run on `http://localhost:8000`

### 5. Test the Flow
```bash
python test_facebook_campaign_flow.py
```

## User Flow

1. **Login** - Authenticate with Facebook access token
2. **Select Ad Account** - Choose which ad account to use
3. **Select Media** - Pick an image or video from HeyGen-generated content
4. **AI Creates Campaign** - Agent generates campaign configuration
5. **Preview** - Review the campaign details
6. **Modify** - Request changes in natural language
7. **Publish** - Upload campaign to Facebook (goes live)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/facebook/authenticate` | POST | Authenticate and get ad accounts |
| `/api/facebook/select_account` | POST | Select ad account |
| `/api/facebook/media` | GET | List available media |
| `/api/facebook/select_media` | POST | Select media for campaign |
| `/api/facebook/campaign/create` | POST | Create campaign with AI |
| `/api/facebook/campaign/preview` | POST | Generate preview |
| `/api/facebook/campaign/modify` | POST | Modify campaign |
| `/api/facebook/campaign/publish` | POST | Publish to Facebook |

## Key Files

- `state_schema.py` - Extended with Facebook fields
- `workflow_graph.py` - Added 8 Facebook campaign nodes
- `facebook_agents.py` - AI agents for campaign management
- `facebook/auth.py` - Facebook authentication
- `media_manager.py` - HeyGen media management
- `server_langgraph.py` - FastAPI server with endpoints
- `test_facebook_campaign_flow.py` - Test script

## Features

✅ Facebook OAuth authentication  
✅ Ad account selection  
✅ HeyGen media integration  
✅ AI-powered campaign creation  
✅ Human-readable previews  
✅ Natural language modifications  
✅ Complete Facebook Ads API integration  
✅ Thread-based session management  

## Safety Notes

⚠️ Campaigns are created in **PAUSED** status by default  
⚠️ Always test with a **sandbox ad account** first  
⚠️ Facebook access tokens **expire** - implement refresh mechanism  
⚠️ **Rate limits** apply to Facebook API calls  

## Documentation

- See `walkthrough.md` for detailed implementation guide
- See `implementation_plan.md` for architecture details
- See `task.md` for development checklist

## Support

For issues or questions, refer to the walkthrough documentation or check the test script for usage examples.
