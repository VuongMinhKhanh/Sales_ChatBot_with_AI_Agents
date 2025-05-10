import json
import time

from langchain.prompts import PromptTemplate

from chatbot.agents.agent_utils import extract_intent
from chatbot.prompts import agent3_followup_prompt
from chatbot.templates import TEMPLATES
from services import get_llm_agent3_followup, get_llm_generic_with_json

from chatbot.agent_registry import register_agent

@register_agent("Agent3")
def agent3_generate_followup(payload):
    # Extract parameters from the payload dictionary.
    user_message   = payload.get("user_message", "")
    chat_history   = payload.get("chat_history", "")
    business_logic = payload.get("business_logic", "")
    user_profile   = payload.get("user_profile", "")
    workflow_stage = payload.get("workflow_stage", "Needs Assessment")
    instruction    = payload.get("instruction", "")
    workflow_stages = payload.get("workflow_stages", "")
    ai_answer      = payload.get(chat_history[-1].content, "")
    agent3_hint    = payload.get("hints", {}).get("Agent3", "")

    # Classify followup template branches
    extracted_intent = extract_intent(user_message, ai_answer)

    followup_template = TEMPLATES.get(extracted_intent.get("intent", ""), "")

    # Create a prompt template.
    prompt_template = PromptTemplate.from_template(agent3_followup_prompt)

    # Create the chain.
    chain = prompt_template | get_llm_agent3_followup()
    
    start = time.time()
    # Invoke the chain with the input data.
    result = chain.invoke({
         "user_message": user_message,  # Using the user_message as the query.
         "chat_history": chat_history,
         "business_logic": business_logic,
         "user_profile": user_profile,
         "workflow_stage": workflow_stage,
         "instruction": instruction,
         "workflow_stages": workflow_stages,
         "ai_answer": ai_answer,
         "followup_template": followup_template,
         "agent3_hint": agent3_hint
    })
    end = time.time()
    print(f"⏱️ Time taken - agent 3: {end - start:.4f} seconds")
    print("Agent 3 followup:", json.loads(result.content).get("followup"))
    return json.loads(result.content), float(f"{end - start:.4f}")