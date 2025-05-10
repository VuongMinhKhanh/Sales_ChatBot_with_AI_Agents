import json
import time

from langchain_core.prompts import PromptTemplate

from chatbot.prompts import agent4_profile_update_prompt
from services import get_llm_generic_with_json


def agent4_update_user_profile(payload):
    """
    Update the user profile based on the latest conversation context.

    Expected payload keys:
      - user_message: Latest message from the user.
      - ai_message: Latest AI response.
      - followup: The followup question if any.
      - user_profile: The current user profile.

    Returns:
      A JSON object in the form:
      {
          "updated_profile": "<updated customer profile>"
      }
    """
    # Extract parameters from the payload dictionary.
    user_message   = payload.get("user_message", "")
    ai_message     = payload.get("ai_message", "")
    followup       = payload.get("followup", "")
    user_profile   = payload.get("user_profile", "")

    # Create the prompt template.
    prompt_template = PromptTemplate.from_template(agent4_profile_update_prompt)

    # Create the chain (using the llm instance).
    chain = prompt_template | get_llm_generic_with_json()

    # Measure processing time.
    start = time.time()
    # Invoke the chain with the gathered input data.
    result = chain.invoke({
         "user_message": user_message,
         "ai_message": ai_message,
         "followup": followup,
         "user_profile": user_profile,
    })
    end = time.time()
    print(f"⏱️ Time taken - agent 4: {end - start:.4f} seconds")

    # Convert the result (assumed to be a JSON string) to a JSON object.
    try:
        data = json.loads(result.content)
        return data["updated_profile"], float(f"{end - start:.4f}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Agent 4: {e}")
        print(f"Raw response from Agent 4: {result.content}")
        # Handle the error appropriately, e.g., return an empty profile or re-prompt Agent 4
        return {
        "updated_profile": ""
      }, float(f"{end - start:.4f}")