# Quick Start Guide - LangGraph Workflow

## Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables**
Create a `.env` file with:
```
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
HEYGEN_API_KEY=your_heygen_key
GOOGLE_API_KEY=your_google_key
```

3. **Start the Server**
```bash
cd AgneticFlow
python server_langgraph.py
```

The server will start on `http://localhost:8000`

## Basic Usage

### 1. Start a New Campaign

```python
import requests

# Scrape a product
response = requests.post("http://localhost:8000/api/workflow/scrape", json={
    "url": "https://example.com/product"
})
data = response.json()
thread_id = data["thread_id"]
print(f"Thread ID: {thread_id}")
print(f"Product: {data['state']['product_data']['title']}")
```

### 2. Analyze Product

```python
# Initial analysis
response = requests.post("http://localhost:8000/api/workflow/analyze", json={
    "thread_id": thread_id
})
analysis = response.json()["state"]["analysis"]
print(f"Analysis: {analysis}")

# Refine analysis with feedback
response = requests.post("http://localhost:8000/api/workflow/analyze", json={
    "thread_id": thread_id,
    "feedback": "Focus more on the target audience demographics"
})
```

### 3. Generate Scripts

```python
# Generate 3 scripts
response = requests.post("http://localhost:8000/api/workflow/generate_scripts", json={
    "thread_id": thread_id
})
scripts = response.json()["state"]["scripts"]
print(f"Generated {len(scripts)} scripts")

# Refine scripts
response = requests.post("http://localhost:8000/api/workflow/generate_scripts", json={
    "thread_id": thread_id,
    "feedback": "Make them more energetic and fun"
})
```

### 4. Select and Refine Script

```python
# Select script 0
response = requests.post("http://localhost:8000/api/workflow/select_script", json={
    "thread_id": thread_id,
    "script_index": 0
})
selected_script = response.json()["state"]["selected_script"]
print(f"Selected: {selected_script[:100]}...")

# Refine selected script
response = requests.post("http://localhost:8000/api/workflow/refine_script", json={
    "thread_id": thread_id,
    "feedback": "Make it shorter and add a call to action"
})
```

### 5. Generate Images

```python
# Generate images
response = requests.post("http://localhost:8000/api/workflow/generate_images", json={
    "thread_id": thread_id
})
images = response.json()["state"]["generated_images"]
print(f"Generated {len(images)} images")

# Refine images
response = requests.post("http://localhost:8000/api/workflow/refine_images", json={
    "thread_id": thread_id,
    "feedback": "Use warmer colors and add more product focus"
})
```

### 6. Generate Audio

```python
response = requests.post("http://localhost:8000/api/workflow/generate_audio", json={
    "thread_id": thread_id
})
audio_url = response.json()["state"]["audio_url"]
print(f"Audio: {audio_url}")
```

### 7. Select Avatar and Generate Video

```python
# Get available avatars
response = requests.get(f"http://localhost:8000/api/workflow/avatars?thread_id={thread_id}")
avatars = response.json()["avatars"]
print(f"Available avatars: {len(avatars)}")

# Select avatar
response = requests.post("http://localhost:8000/api/workflow/select_avatar", json={
    "thread_id": thread_id,
    "avatar_id": avatars[0]["avatar_id"]
})

# Generate video
response = requests.post("http://localhost:8000/api/workflow/generate_video", json={
    "thread_id": thread_id
})
video_id = response.json()["state"]["video_id"]
print(f"Video ID: {video_id}")
```

## Navigation Examples

### Go Back to Previous Step

```python
# Navigate back to analysis
response = requests.post("http://localhost:8000/api/workflow/navigate", json={
    "thread_id": thread_id,
    "navigation_intent": "go to analyze"
})

# Update analysis
response = requests.post("http://localhost:8000/api/workflow/analyze", json={
    "thread_id": thread_id,
    "feedback": "Add more details about competitive positioning"
})
```

### Chat-Based Editing

```python
# Chat at current step (auto-routes)
response = requests.post("http://localhost:8000/api/workflow/chat", json={
    "thread_id": thread_id,
    "message": "Make the script more conversational"
})
```

### Get Current State

```python
# Check current state
response = requests.get(f"http://localhost:8000/api/workflow/state/{thread_id}")
state = response.json()["state"]
print(f"Current step: {state['current_step']}")
print(f"Iterations: {state['iteration_count']}")
```

## Frontend Integration

### React/Next.js Example

```typescript
// api.ts
const API_BASE = 'http://localhost:8000/api/workflow';

export const workflowAPI = {
  scrape: async (url: string) => {
    const res = await fetch(`${API_BASE}/scrape`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    return res.json();
  },

  analyze: async (threadId: string, feedback?: string) => {
    const res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: threadId, feedback })
    });
    return res.json();
  },

  navigate: async (threadId: string, intent: string) => {
    const res = await fetch(`${API_BASE}/navigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: threadId, navigation_intent: intent })
    });
    return res.json();
  },

  chat: async (threadId: string, message: string) => {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: threadId, message })
    });
    return res.json();
  }
};
```

## Key Concepts

1. **Thread ID**: Each campaign session has a unique `thread_id` that tracks state
2. **Navigation Intent**: Use phrases like "go to analyze" or "go back to scripts"
3. **Feedback**: Provide feedback at any step to refine output
4. **State Persistence**: All state is maintained per thread_id
5. **Context Awareness**: Previous steps are always available when navigating

## Troubleshooting

### Server won't start
- Check that all environment variables are set
- Ensure port 8000 is available
- Verify all dependencies are installed

### State not persisting
- Ensure you're using the same `thread_id` across requests
- Check that the server is maintaining sessions correctly

### Navigation not working
- Use clear navigation intents (e.g., "go to analyze")
- Check that prerequisites are met (e.g., need product data before analysis)

### Agent errors
- Verify API keys are correct
- Check that OpenAI API has credits
- Ensure network connectivity

## Next Steps

- See `LANGGRAPH_README.md` for detailed architecture
- See `ARCHITECTURE_SUMMARY.md` for overview
- Update frontend to use new endpoints
- Add error handling and validation
- Implement state persistence (database)

