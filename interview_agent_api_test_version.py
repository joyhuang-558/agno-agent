"""
Interview Agent API Service
Exposes Interview Agent through AgnoOS for use with control panel
"""
import os
from textwrap import dedent
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS
from pydantic import BaseModel, Field
from typing import List, Optional

# Load environment variables from .env file if it exists
load_dotenv()

# Check if OPENROUTER_API_KEY is set
if not os.environ.get("OPENROUTER_API_KEY"):
    raise ValueError("Set OPENROUTER_API_KEY in your environment or .env file. Do not commit keys.")

# Initialize database (SqliteDb for persistence)
DB = SqliteDb(db_file="agno.db")

# --- Context (simple context engineering) ---
INTERVIEW_TYPE = "technical"
ROLE = "Data Scientist"

# --- Structured output: one interview turn = question + type + expected key points ---
class InterviewTurn(BaseModel):
    """One interviewer turn: the question to ask and what to look for in the answer."""
    current_question: Optional[str] = Field(None, description="The interview question to ask the candidate. Only provide this when the user is asking for a new question.")
    question_type: Optional[str] = Field(None, description="e.g. technical, behavioral, system_design")
    expected_key_points: Optional[List[str]] = Field(None, description="Key points or themes to look for in a good answer. Only provide this AFTER the candidate has answered a question, to show them the correct answer.")
    feedback: Optional[str] = Field(None, description="Feedback on the candidate's answer. Only provide this AFTER the candidate has answered a question.")

# --- Interview Agent: single agent, structured output, context in instructions ---
interview_agent = Agent(
    name="InterviewAgent",
    model=OpenRouter(
        id="openai/gpt-4o-mini",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    ),
    instructions=dedent(f"""
        You are a professional interviewer conducting a mock data science interview.
        Interview type: {INTERVIEW_TYPE}.
        Role: {ROLE}.
        Focus on data science topics: statistics, ML, Python/pandas, SQL, A/B testing, metrics, etc.
        
        IMPORTANT RULES - You have THREE different response modes:
        
        1. WHEN USER ASKS FOR A QUESTION (e.g., "give me a question", "I'm ready", "next question", "ask me something"):
           - Provide ONLY the question in 'current_question' field
           - Set 'question_type' appropriately  
           - DO NOT provide 'expected_key_points' or 'feedback' (set them to null)
           - This is the question-asking phase - candidate hasn't answered yet, so don't reveal the answer
        
        2. WHEN USER PROVIDES AN ANSWER (they've answered your previous question):
           - First, provide 'expected_key_points' with the correct answer/key points they should have mentioned
           - Provide 'feedback' evaluating their answer (what they got right, what they missed, brief comment)
           - Then ask a NEW question in 'current_question' for the next round
           - Set 'question_type' for the new question
        
        3. WHEN USER SAYS SOMETHING ELSE (greetings, questions, unclear input, "I don't know", requests for clarification, etc.):
           - Politely acknowledge their input in the 'feedback' field
           - If they seem confused or asking for clarification, provide brief guidance
           - Then ask a NEW question in 'current_question' to keep the interview moving
           - Set 'question_type' appropriately
           - Set 'expected_key_points' to null (no previous answer to evaluate)
           - Examples:
             * "Hello" → Acknowledge, then ask first question
             * "I don't know" → Encourage them, then ask a new/different question
             * "Can you explain?" → Briefly clarify if needed, then ask a new question
             * Unclear input → Politely ask for clarification, then provide a new question
        
        Use conversation history to:
        - Remember what questions you've already asked (don't repeat them)
        - Remember the candidate's previous answers
        - Build on previous topics and create a coherent interview flow
        
        Be concise and professional. Always provide at least a question in 'current_question' to keep the interview progressing.
        """),
    db=DB,
    add_history_to_context=True,
    output_schema=InterviewTurn,
    use_json_mode=True,
    retries=3,
)

# --- Create AgentOS and expose as API ---
agent_os = AgentOS(agents=[interview_agent])
app = agent_os.get_app()

if __name__ == "__main__":
    # Start the server using uvicorn
    import uvicorn
    # The server will run on http://localhost:8000 by default
    # Use import string format to enable reload functionality
    uvicorn.run("interview_agent_api_test_version:app", host="0.0.0.0", port=8000, reload=True)
