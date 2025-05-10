import json

from langchain_core.messages import HumanMessage, AIMessage

from services import get_redis_client

redis_client = get_redis_client()

def clear_chat_history(conversation_id):
    """Clear chat history from Redis."""
    redis_client.delete(f"chat_history:{conversation_id}")
    print(f"Cleared chat history for conversation_id: {conversation_id}")


def serialize_chat_history(chat_history):
    serialized_history = []
    for message in chat_history:
        if isinstance(message, HumanMessage):
            serialized_history.append({
                "type": "HumanMessage",
                "content": message.content
            })
        else:  # For other message types
            serialized_history.append({
                "type": "AiMessage",
                "content": message.content
            })
    return serialized_history


def store_chat_history(conversation_id, chat_history):
    """Store chat history in Redis."""
    chat_history_serialized = serialize_chat_history(chat_history)
    # print("chat_history_serialized", chat_history_serialized)
    redis_client.set(f"chat_history:{conversation_id}", json.dumps(chat_history_serialized))


def get_chat_history(conversation_id):
    """Retrieve chat history from Redis."""
    history = redis_client.get(f"chat_history:{conversation_id}")
    if history:
        deserialized_history = json.loads(history)
        return [
            HumanMessage(content=msg["content"]) if msg["type"] == "human" else AIMessage(content=msg["content"])
            for msg in deserialized_history
        ]
    return []


def is_assigned(conversation_id):
    """Check if a conversation is assigned to a consultant."""
    return redis_client.exists(f"assigned_conversation:{conversation_id}")


def mark_assigned(conversation_id, consultant_id):
    """Mark a conversation as assigned in Redis with a TTL of 1 hour."""
    redis_client.setex(f"assigned_conversation:{conversation_id}", 3600, consultant_id)


def remove_assigned(conversation_id):
    """Remove assigned status for a conversation."""
    redis_client.delete(f"assigned_conversation:{conversation_id}")