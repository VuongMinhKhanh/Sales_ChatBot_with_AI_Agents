from flask import Flask, render_template, jsonify, request

from bootstrap import initialize_system
from chatbot.agent_core import chatbot_run
from chatwoot.chatwoot_api import send_typing_indicator, assign_to_consultant, send_message_to_chatwoot, \
    update_chatwoot_user, set_unassigned
from config import WEAVIATE_CLASS_NAME, AGENT_ID
from redis_store.redis_cache import get_chat_history, mark_assigned, clear_chat_history, remove_assigned
from dotenv import load_dotenv
import os
import traceback

from services import get_weaviate_client, get_redis_client
from test_update import adjust_columns_by_patch_data
import json

# Load environment variables from .env file
load_dotenv()

# Flask App Initialization
app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/test-api', methods=['POST', 'PATCH'])
def adjust_columns_by_patch_data():
    if request.content_type == 'application/json':
        data = request.get_json()
    elif request.content_type == 'application/x-www-form-urlencoded':
        data = request.form.to_dict()
    else:
        return jsonify({"status": "error", "message": "Unsupported Media Type"}), 415

    # print(data)
    # print(data.get("id"))
    adjust_columns_by_patch_data(get_weaviate_client(), data, WEAVIATE_CLASS_NAME)

    return jsonify({
        "status": "success",
        "message": "Data received successfully!",
        "received_data": data
    }), 200


@app.route('/workflow-update', methods=['PATCH'])
def patch_update():
    data = request.json  # Get JSON payload from n8n
    # print("Received PATCH request:", data)  # Log data to console

    # Update only provided fields (partial update)
    workflow_data = json.loads(get_redis_client().get("sales_workflow"))
    # print(data)
    # print(workflow_data)

    # Track only the changed fields
    updated_data = {}

    if workflow_data is None:
        workflow_data = {}  # If no data exists, initialize an empty dictionary

    for key, value in data.items():
        if key not in workflow_data or workflow_data[key] != value:
            workflow_data[key] = value
            updated_data[key] = value  # Store only changed fields

    if updated_data:
        # for key, value in updated_data.items():
        #     redis_client.hset("sales_workflow", key, json.dumps(value))  # Update only the changed fields
        get_redis_client().set("sales_workflow", json.dumps(data))
        print("sales_workflow", get_redis_client().get("sales_workflow"))
        pass
    else:
        print("There is no changes")

    return jsonify({
        "message": "Workflow partially updated",
        "updated_data": updated_data  # Return only the changed fields
    }), 200


@app.route("/api/webhook", methods=["POST"])
def webhook():
    try:
        body = request.json
        # print("Received payload:", json.dumps(body, indent=2))
        event_type = body.get("event")
        # print(f"Received event: {event_type}")

        conversation = body.get("conversation", {})
        messages = conversation.get("messages", [])

        # conversation_id = conversation.get("id")
        # print(f"Conversation ID: {conversation_id}")

        if messages and event_type == "message_created":
            last_message = messages[-1]
            # print(f"Last message: {last_message}")

            conversation_id = last_message.get("conversation_id")
            # print(f"Conversation ID: {conversation_id}")

            user_message = last_message.get("content")
            # print(f"user_message: {user_message}")

            sender_type = last_message.get("sender_type")
            # print(f"Sender Type: {sender_type}")

            assignee_id = last_message.get("conversation", {}).get("assignee_id", None)
            # print(f"Assignee ID: {assignee_id}")

        else:
            # print("No messages found in this event.")
            conversation_id, user_message, sender_type, assignee_id = None, None, None, None

        if event_type == "conversation_status_changed":
            if body.get("status") == "resolved":
                conversation_id = body.get("id")
                if id:
                    send_message_to_chatwoot(conversation_id, os.getenv("RESET_TEXT"))
                else:
                    send_message_to_chatwoot(conversation_id, os.getenv("BACK_TO_BOT"))

                print(f"Conversation {conversation_id} marked as resolved.")
                remove_assigned(conversation_id)
                clear_chat_history(conversation_id)
                set_unassigned(conversation_id)  # Assign the conversation back to None
                CONTACT_ID = body["meta"]["sender"]["id"]
                update_chatwoot_user(CONTACT_ID, "")

                return jsonify({"status": "success", "message": "Conversation resolved and unassigned."}), 200
            else:
                print("Conversation ID not found.")
                return jsonify({"status": "error", "message": "Conversation ID not found."}), 200

        # Ignore the message if it's not from a user
        if sender_type != "Contact":
            return jsonify({"status": "ignored", "message": "Message is not from a user."}), 200

        # Ignore the message if the conversation is assigned to a consultant
        if assignee_id is not None:
            print(f"Conversation {conversation_id} is assigned to consultant {assignee_id}. Chatbot is disabled.")
            return jsonify({"status": "ignored", "message": "Chatbot is disabled for assigned conversation."}), 200

        # Ignore the message if content or conversation_id is missing
        if not user_message or not conversation_id:
            print("Missing user_message or conversation_id.")
            return jsonify({"status": "ignored", "message": "Missing user_message or conversation_id."}), 200

        # Process the message using the chatbot
        if user_message.lower() in ["talk to consultant", "need human help", "consultant please", "tuvanvien"]:
            send_message_to_chatwoot(conversation_id, os.getenv("ASSIGNING_TEXT"))
            assign_to_consultant(conversation_id)
            mark_assigned(conversation_id, AGENT_ID)
            return jsonify({"status": "success", "message": "Assigned to consultant"}), 200

        # Init the vars from external memory
        sender = body.get("sender")
        user_profile = sender.get("additional_attributes").get("description", "")
        predicted_stage = ""
        contact_id = sender["id"]
        chat_history = get_chat_history(conversation_id)

        ### Start of chatbot run
        chatbot_run(user_message, user_profile, predicted_stage, conversation_id, contact_id, chat_history)
        ### End of chatbot run
        return jsonify({"status": "success", "message": "Chatbot response processed."}), 200

    except Exception as e:
        print(f"Unexpected error in webhook: {e}")
        traceback.print_exc()  # ✅ This shows the exact line that caused the error
        # ❌ Disable Typing Indicator
        send_typing_indicator(conversation_id, "off")
        return jsonify({"status": "error", "details": str(e)}), 500


if __name__ == '__main__':
    initialize_system()
    app.run(debug=True, port=5000)
