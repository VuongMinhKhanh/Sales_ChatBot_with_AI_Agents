import time
from chatbot.agent_registry import agent_registry
from chatbot.agents.agent1 import agent1_dispatch_agents
from chatbot.agents.agent4 import agent4_update_user_profile
from chatbot.agents.agent_utils import handle_followup_response
from chatbot.agents.utils import format_strategies_for_prompt, compact_feedback_list
from chatbot.workflow_definitions import get_workflow_stages, get_workflow
from chatwoot.chatwoot_api import update_chatwoot_user, send_typing_indicator


def dispatcher(actions_list, payload, conversation_id):
    responses = []

    if "chat_history" not in payload or not isinstance(payload["chat_history"], list):
        payload["chat_history"] = []

    # carry a dict of hints per agent
    payload.setdefault("hints", {})

    # Loop through each action and dynamically call the corresponding function
    for action in actions_list:
        time_consumed = None
        # ✅ Enable Typing Indicator
        send_typing_indicator(conversation_id, "on")
        agent_name = action["agent"]
        hint       = action.get("payload", {}).get("hint")

        # stash this action’s hint under payload["hints"]
        payload["hints"][agent_name] = hint

        # Retrieve the agent function from the registry
        agent_function = agent_registry.get(agent_name)
        if agent_function is not None:
            response, time_consumed = agent_function(payload)
        else:
            response = f"Error: {agent_name} is not registered."
        responses.append({
            "agent": agent_name,
            "task": action["task"],
            "response": response,
            "time_consumed": time_consumed
        })

        # get answers from each agent, will fix for more dynamic
        answer = response.get("answer", None)
        if answer:
            handle_followup_response(conversation_id, answer, payload["chat_history"])

        followup = response.get("followup", None)
        if followup and followup.lower() != "none":
            handle_followup_response(conversation_id, followup, payload["chat_history"])

        # ❌ Disable Typing Indicator
        send_typing_indicator(conversation_id, "off")

    return responses


def chatbot_run(user_message,
                user_profile,
                predicted_stage,
                conversation_id,
                contact_id,
                chat_history=None
                ):
    """
    Simulate the chatbot execution workflow.

    Inputs:
      user_message: A string from the user (e.g. "Tôi muốn mua micro shure")
      chat_history: Optional list of previous conversation messages (default: empty list)

    Returns:
      A dict with agent result keys:
        - "agent1": The full result from Agent 1 (Orchestrator)
        - "agent2": The result from Agent 2 (Product Info Agent)
        - "agent3": The result from Agent 3 (Followup Agent)

      # agent1: Orchestrator output, including query_and_stage with semantic query and workflow stage.
      # agent2: Chatbot answer output (when not in Greeting stage)
      # agent3: Chatbot followup output (when not in Greeting stage)
    """
    if chat_history is None:
        chat_history = []

    try:
        workflow_stages = get_workflow_stages().keys()
    except Exception:
        workflow_stages = "Greeting, Needs Assessment, Qualification, Product Presentation, Objection Handling, Closing"

    total_start_time = time.time()

    # ---------------------------
    # Step 1: Agent 1 (Orchestrator)
    # ---------------------------

    # print(chat_history)
    agent1_result, time_agent1 = agent1_dispatch_agents(chat_history, predicted_stage, user_profile, user_message, workflow_stages)

    # check Agent 1 answer
    agent1_answer = agent1_result.get("query_and_stage").get("answer")
    # print("agent1_answer:", agent1_answer)
    # return

    if agent1_answer:
        print("Agent 1 answer:", agent1_answer)
        handle_followup_response(conversation_id, agent1_answer, chat_history)
        return

    # Move on to other Agents
    actions = agent1_result.get("actions", [])
    query_and_stage = agent1_result.get("query_and_stage", {})
    business_logic = agent1_result.get("retrieval_context", {}).get("business_logic", [])
    optimized_business_logic = format_strategies_for_prompt(business_logic)
    user_feedback = agent1_result.get("retrieval_context", {}).get("user_feedback", [])
    optimized_user_feedback = compact_feedback_list(user_feedback)

    # ---------------------------
    # Step 2: Dispatch actions to Agent 2 and Agent 3
    # ---------------------------
    payload = {
        "user_message": query_and_stage.get("semantic_query", ""),
        "workflow_stage": query_and_stage.get("workflow_stage", ""),
        "chat_history": chat_history,
        "business_logic": optimized_business_logic,
        "user_feedback": optimized_user_feedback,
        "user_profile": user_profile,
        "workflow_stages": workflow_stages,
        "instruction": get_workflow(query_and_stage.get("workflow_stage", "")),
    }

    # Dispatcher calls the functions registered.
    dispatcher(actions, payload, conversation_id)

    # Update the user profile if needed.
    updated_user_profile, time_agent4 = agent4_update_user_profile(payload)
    print("Updated User Profile:", updated_user_profile)
    update_chatwoot_user(contact_id, updated_user_profile)
    total_end_time = time.time()
    print(f"⏱️⏱️⏱️ Total execution time: {total_end_time - total_start_time:.4f} seconds")

    return
