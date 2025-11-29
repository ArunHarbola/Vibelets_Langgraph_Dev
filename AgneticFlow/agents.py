"""
LangChain agents for each step of the workflow
Each agent is specialized for its task and supports chat-based refinement
"""
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
import json
import re
from config import Config


class AnalysisAgent:
    """Agent for product analysis with chat-based refinement"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=Config.OPENAI_API_KEY
        )
    
    async def analyze(self, product_data: Dict, feedback_history: List[str] = None) -> Dict:
        """Generate or refine product analysis"""
        feedback_history = feedback_history or []
        
        if not feedback_history:
            # Initial analysis
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert marketing analyst specializing in product analysis and target audience identification."),
                ("human", """
Analyze this product and provide a detailed analysis:

Product Name: {title}
Description: {description}
Price: {price}
Additional Context: {raw_text}

Provide:
1. Product Category and Key Features
2. Target Audience (demographics, psychographics, pain points)
3. Unique Selling Propositions (USPs)
4. Marketing Angles and Emotional Triggers
5. Competitive Positioning

Format as JSON with keys: category, features, target_audience, usps, marketing_angles, positioning
""")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            result = await chain.ainvoke({
                "title": product_data.get('title', ''),
                "description": product_data.get('description', ''),
                "price": product_data.get('price', ''),
                "raw_text": product_data.get('raw_text', '')
            })
        else:
            # Refinement based on feedback
            latest_feedback = feedback_history[-1]
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert marketing analyst. Refine the product analysis based on user feedback while maintaining accuracy."),
                ("human", """
Current Analysis:
{current_analysis}

Product Context:
Product Name: {title}
Description: {description}
Price: {price}

User Feedback: {feedback}

Refine the analysis addressing the user's feedback. Maintain the JSON format with keys: category, features, target_audience, usps, marketing_angles, positioning
""")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            result = await chain.ainvoke({
                "current_analysis": json.dumps(product_data.get('current_analysis', {}), indent=2),
                "title": product_data.get('title', ''),
                "description": product_data.get('description', ''),
                "price": product_data.get('price', ''),
                "feedback": latest_feedback
            })
        
        try:
            return json.loads(result)
        except:
            return {"analysis": result}


class ScriptGenerationAgent:
    """Agent for generating ad scripts with chat-based refinement"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.8,
            openai_api_key=Config.OPENAI_API_KEY
        )
    
    def _parse_scripts(self, text: str) -> List[str]:
        """Parse scripts from LLM output"""
        pattern = r'SCRIPT\s*(?:\[?\d+\]?)?:?(.*?)(?=SCRIPT\s*(?:\[?\d+\]?)?:?|$)'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        scripts = []
        for match in matches:
            cleaned = match.strip()
            cleaned = re.sub(r'-+$', '', cleaned).strip()
            if cleaned:
                scripts.append(cleaned)
        
        if not scripts:
            if '---' in text:
                parts = text.split('---')
                scripts = [p.strip() for p in parts if p.strip()]
            else:
                scripts = [text.strip()]
        
        return scripts
    
    async def generate_scripts(self, product_data: Dict, analysis: Dict, feedback_history: List[str] = None) -> List[str]:
        """Generate or refine ad scripts"""
        feedback_history = feedback_history or []
        
        if not feedback_history:
            # Initial generation
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a creative copywriter specializing in short-form video ad scripts for social media."),
                ("human", """
Create 3 unique short-form video ad scripts (30-45 seconds each) for this product:

Product: {title}
Target Audience: {target_audience}
USPs: {usps}
Marketing Angles: {marketing_angles}

Each script should:
- Hook viewers in the first 3 seconds
- Address a pain point or desire
- Highlight key benefits
- Include a clear call-to-action
- Be conversational and engaging
- Use AIDA framework (Attention, Interest, Desire, Action)

Format each script with:
SCRIPT [1/2/3]:
[Script content - spoken word only, 30-45 seconds when read aloud, around 100 words max.]
---

Make each script distinctly different in approach (problem-solution, testimonial-style, lifestyle-focused).
Output only the voice over without additional commentary.
""")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            result = await chain.ainvoke({
                "title": product_data.get('title', ''),
                "target_audience": str(analysis.get('target_audience', '')),
                "usps": str(analysis.get('usps', '')),
                "marketing_angles": str(analysis.get('marketing_angles', ''))
            })
        else:
            # Refinement
            latest_feedback = feedback_history[-1]
            scripts_text = ""
            for i, script in enumerate(product_data.get('current_scripts', []), 1):
                scripts_text += f"\nSCRIPT {i}:\n{script}\n---\n"
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a creative copywriter. Refine the ad scripts based on user feedback while maintaining quality and effectiveness."),
                ("human", """
Current Scripts:
{current_scripts}

Product: {title}
Target Audience: {target_audience}
USPs: {usps}

User Feedback: {feedback}

Refine the 3 scripts addressing the user's feedback. Maintain the format:
SCRIPT [1/2/3]:
[Script content]
---

Keep scripts 30-45 seconds when read aloud (around 100 words max each).
""")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            result = await chain.ainvoke({
                "current_scripts": scripts_text,
                "title": product_data.get('title', ''),
                "target_audience": str(analysis.get('target_audience', '')),
                "usps": str(analysis.get('usps', '')),
                "feedback": latest_feedback
            })
        
        return self._parse_scripts(result)
    
    async def refine_script(self, script: str, feedback: str) -> str:
        """Refine a single selected script"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a creative copywriter. Modify the script based on specific user requests while maintaining effectiveness."),
            ("human", """
Current Script:
{current_script}

User Request: {feedback}

Provide the modified script (30-45 seconds when read aloud). Output only the script content without labels or commentary.
""")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "current_script": script,
            "feedback": feedback
        })
        
        return result.strip()


class ImageGenerationAgent:
    """Agent for generating images with chat-based refinement"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=Config.OPENAI_API_KEY
        )
        # We'll still use the ImageGenerator for actual generation
        from image_generation import ImageGenerator
        self.image_gen = ImageGenerator()
    
    async def generate_prompt(self, product_data: Dict, script: str, analysis: Dict = None, feedback: str = None) -> str:
        """Generate or refine image generation prompt using LLM"""
        
        if feedback:
            # Refine prompt based on feedback
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are an expert in creating detailed image generation prompts for commercial advertisements."),
                ("human", """
Current Image Generation Prompt:
{current_prompt}

Product Context:
- Product: {title}
- Description: {description}
- Script Context: {script_context}

User Feedback: {feedback}

Create a refined, detailed image generation prompt that addresses the user's feedback. 
The prompt should describe a professional commercial advertisement static featuring the product.
Include details about setting, style, composition, lighting, and mood.
Keep it focused on the product as the focal point.
""")
            ])
            
            chain = prompt_template | self.llm | StrOutputParser()
            result = await chain.ainvoke({
                "current_prompt": product_data.get('current_prompt', ''),
                "title": product_data.get('title', ''),
                "description": product_data.get('description', ''),
                "script_context": script[:200],
                "feedback": feedback
            })
            return result.strip()
        else:
            # Initial prompt generation
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are an expert in creating detailed image generation prompts for commercial advertisements."),
                ("human", """
Create a detailed image generation prompt for a commercial advertisement featuring this product:

Product: {title}
Description: {description}
Script Context: {script_context}
Target Audience: {target_audience}
Marketing Angle: {marketing_angle}

The prompt should describe:
- A professional commercial advertisement static
- High-quality, aesthetic setting suitable for marketing
- Product as the focal point
- Modern, premium, commercial photography style
- Appropriate mood and lighting based on the marketing angle

Output only the prompt, no additional commentary.
""")
            ])
            
            chain = prompt_template | self.llm | StrOutputParser()
            result = await chain.ainvoke({
                "title": product_data.get('title', ''),
                "description": product_data.get('description', ''),
                "script_context": script[:200],
                "target_audience": str(analysis.get('target_audience', '')) if analysis else '',
                "marketing_angle": str(analysis.get('marketing_angles', '')) if analysis else ''
            })
            return result.strip()
    
    def generate_images(self, product_url: str, image_prompt: str, num_images: int = 2) -> List[str]:
        """Generate images using the refined prompt"""
        return self.image_gen.generate_ad_creatives_with_prompt(
            product_url, 
            image_prompt, 
            num_images
        )


class NavigationAgent:
    """Agent for determining navigation intent from user messages"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            openai_api_key=Config.OPENAI_API_KEY
        )
    
    async def analyze_intent(self, state: Dict) -> Dict[str, Any]:
        """Analyze user message to determine navigation intent"""
        messages = state.get("messages", [])
        if not messages:
            return {"intent": "continue"}
            
        # Get the last user message
        last_user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content")
                break
        
        if not last_user_message:
            return {"intent": "continue"}
            
        current_step = state.get("current_step", "scrape")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a navigation router for an ad campaign generation workflow.
Your job is to determine where the user wants to go based on their message and the current step.

Workflow Steps:
1. scrape (Input URL)
2. analyze (Product Analysis)
3. generate_scripts (Create Ad Scripts)
4. select_script (Choose one script)
5. refine_script (Edit selected script)
6. generate_images (Create visuals)
7. refine_images (Edit visuals)
8. generate_audio (Voiceover)
9. select_avatar (Choose presenter)
10. generate_video (Final video)

Rules:
- If user says "next", "looks good", "continue", or approves current output -> return "next"
- If user wants to change something from a previous step (e.g., "change target audience") -> return the name of that step (e.g., "analyze")
- If user explicitly asks to go to a step -> return that step name
- If user provides feedback for the CURRENT step (e.g., "make it funnier" while in generate_scripts) -> return "stay" (to refine)
- If user wants to stop -> return "complete"

Output JSON:
{{
    "intent": "next" | "stay" | "complete" | "step_name",
    "reasoning": "brief explanation"
}}
"""),
            ("human", """
Current Step: {current_step}
User Message: {user_message}

Determine the navigation intent.
""")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "current_step": current_step,
            "user_message": last_user_message
        })
        
        try:
            # Clean up potential markdown code blocks
            cleaned_result = result.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_result)
        except:
            print(f"Failed to parse navigation intent: {result}")
            return {"intent": "stay"}


