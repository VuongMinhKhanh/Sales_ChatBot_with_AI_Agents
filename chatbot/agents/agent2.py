import time
from services import initialize_rag
from chatbot.agent_registry import register_agent

@register_agent("Agent2")
def agent2_retrieve_product_info(payload):
    # Extract parameters from the payload dictionary.
    user_message   = payload.get("user_message", "")
    chat_history   = payload.get("chat_history", [])
    business_logic = payload.get("business_logic", [])
    user_profile   = payload.get("user_profile", "")
    workflow_stage = payload.get("workflow_stage", "Needs Assessment")
    user_feedback  = payload.get("user_feedback", "")
    instruction    = payload.get("instruction", "")
    agent2_hint    = payload.get("hints", {}).get("Agent2", "")
    contextualized_query = payload.get("contextualized_query", "")
    # print("agent2_hint", agent2_hint)

    start = time.time()
    # Invoke the RAG system using the extracted parameters.
    # Note: Replace 'rag.invoke' with your actual RAG system call.
    rag = initialize_rag()
    result = rag.invoke({
         "input": user_message,
         "chat_history": chat_history,
         "business_logic": business_logic,
         "user_profile": user_profile,
         "workflow_stage": workflow_stage,
         "instruction": instruction,
         "user_feedback": user_feedback,
         "agent2_hint": agent2_hint,
         "contextualized_query": contextualized_query
    })
    end = time.time()
    print(f"⏱️ Time taken - agent 2: {end - start:.4f} seconds")
    print("agent 2 answer:", result["answer"])
    return result, float(f"{end - start:.4f}")
