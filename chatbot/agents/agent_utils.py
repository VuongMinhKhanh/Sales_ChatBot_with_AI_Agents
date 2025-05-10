from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, ToolCall
import json

from chatbot.prompts import extract_intent_prompt
from chatbot.templates import TEMPLATES
from chatwoot.chatwoot_api import send_message_to_chatwoot
from redis_store.redis_cache import store_chat_history
from services import get_llm_generic_with_json


def extract_intent(user_message: str, ai_answer: str) -> str:
    """
    Classify the user message into an archetype (called 'intent') and extract needed slots,
    then assign a confidence (0.0–1.0). Return EXACTLY JSON with keys:
      - intent: one of our archetypes
      - confidence: float

    Example output:
    {
      "intent": "technical_fit",
      "confidence": 0.87
    }
    """
    prompt_template = PromptTemplate.from_template(extract_intent_prompt)

    # Create the chain.
    chain = prompt_template | get_llm_generic_with_json()

    response = chain.invoke({
        "user_message": user_message,
        "ai_answer": ai_answer,
        "template_keys": ", ".join(TEMPLATES.keys())
    })
    # debug print to verify
    # print("⏺ extractor raw:", response.content)
    return json.loads(response.content)


def handle_followup_response(conversation_id, ai_response, chat_history):
    """
    Send a follow-up message to Chatwoot, update local chat history, and store it.

    Args:
        conversation_id (str): Chatwoot conversation ID.
        ai_response (string): The AI message.
        chat_history (List[BaseMessage]): LangChain message list (e.g., [HumanMessage, AIMessage...])
    """

    # 1. Send to Chatwoot
    send_message_to_chatwoot(conversation_id, ai_response)

    # 2. Append to local history
    chat_history.append(AIMessage(content=ai_response))

    # 3. Store updated history
    store_chat_history(conversation_id, chat_history)
