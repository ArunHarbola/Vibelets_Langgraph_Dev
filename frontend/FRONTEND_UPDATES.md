# Frontend Updates - LangGraph Integration

## Overview

The frontend has been updated to use the new LangGraph workflow API with:
- ✅ Step indicators and navigation UI
- ✅ Back/forward buttons for bidirectional navigation
- ✅ Chat interface for each step
- ✅ Context-aware state management with `thread_id`

## New Files

### 1. `src/lib/workflowApi.ts`
New API client for LangGraph workflow endpoints:
- Manages `thread_id` automatically
- Provides methods for all workflow steps
- Supports navigation and chat-based editing

### 2. `src/components/WorkflowChatInterface.tsx`
New main chat interface component with:
- **Step Progress Bar**: Visual indicators for all 10 steps
- **Navigation Buttons**: Back/forward buttons in header
- **Clickable Steps**: Click any step to navigate directly
- **Chat Integration**: Chat input works at every step
- **State Management**: Tracks workflow state and updates UI accordingly

## Updated Files

### 1. `src/app/page.tsx`
- Now uses `WorkflowChatInterface` instead of `ChatInterface`

### 2. `src/components/VideoGeneration.tsx`
- Updated to use `workflowApi` instead of old `api`
- Integrates with workflow state management

## Features

### Step Navigation

The workflow has 10 steps:
1. **Scrape** - Product URL scraping
2. **Analyze** - Product analysis (editable via chat)
3. **Scripts** - Generate 3 scripts (editable via chat)
4. **Select** - Choose a script
5. **Refine** - Refine selected script (editable via chat)
6. **Images** - Generate images (editable via chat)
7. **Refine Images** - Refine images (editable via chat)
8. **Audio** - Generate audio
9. **Avatar** - Select HeyGen avatar
10. **Video** - Generate lipsynced video

### Visual Indicators

- **Completed Steps**: Green background with checkmark
- **Current Step**: Indigo background with ring
- **Pending Steps**: Gray background

### Navigation

- **Back Button**: Navigate to previous step (preserves context)
- **Forward Button**: Navigate to next step (if prerequisites met)
- **Click Steps**: Jump directly to any step
- **Context Preservation**: All previous work is maintained

### Chat Interface

- **Step-Aware**: Input placeholder changes based on current step
- **Chat Editing**: Type feedback at any step to refine output
- **Auto-Routing**: Chat messages automatically route to appropriate workflow step

## Usage

### Starting a Campaign

1. User pastes product URL
2. System scrapes and shows product images
3. User continues to analysis
4. User can refine analysis via chat
5. Continue through workflow steps

### Navigating Between Steps

1. **Click step indicator** to jump to that step
2. **Use back/forward buttons** for sequential navigation
3. **Type in chat** to refine current step
4. **All context is preserved** when navigating

### Chat-Based Editing

At any step, users can type feedback:
- Analysis: "Focus more on millennials"
- Scripts: "Make them funnier"
- Images: "Use warmer colors"
- Script refinement: "Make it shorter"

## API Integration

All API calls use the workflow endpoints:
- `/api/workflow/scrape`
- `/api/workflow/analyze`
- `/api/workflow/generate_scripts`
- `/api/workflow/navigate`
- `/api/workflow/chat`
- etc.

The `thread_id` is automatically managed by `workflowApi`.

## State Management

The component maintains:
- `currentStep`: Current workflow step
- `workflowState`: Complete workflow state from backend
- `messages`: Chat message history
- `threadId`: Session identifier (managed by workflowApi)

## UI Components

### Header
- Logo and title
- Back/forward navigation buttons
- Step progress bar

### Chat Area
- Message history
- Component rendering (AnalysisCard, ScriptSelection, etc.)
- Loading indicators

### Input Area
- Text input with step-aware placeholder
- Send button
- Current step indicator

## Migration Notes

The old `ChatInterface` component is still available but not used. The new `WorkflowChatInterface` provides:
- Better navigation
- Context awareness
- Step indicators
- Improved UX

## Next Steps

1. Add error handling UI
2. Add loading states for navigation
3. Add confirmation dialogs for navigation
4. Add state persistence (localStorage)
5. Add undo/redo functionality
6. Add step validation before navigation

