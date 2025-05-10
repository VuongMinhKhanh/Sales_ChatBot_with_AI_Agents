# chatbot/bootstrap.py
from chatbot.agents.agent2 import agent2_retrieve_product_info
from chatbot.agents.agent3 import agent3_generate_followup
from services import (
    get_openai_embeddings,
    get_llm_agent1_dispatch,
    get_weaviate_client,
    get_qdrant_client,
    get_docsearch, get_llm_generic, get_llm_generic_with_json, get_llm_agent2_contextualization,
    get_llm_agent2_response, get_llm_agent3_followup, get_redis_client
)
from chatbot.vectorstore import get_retriever
from chatbot.agent_registry import agent_registry, register_agent


def initialize_system():
    """
    Bootstrap the chatbot system: eager-initialize all heavy clients,
    warm up vectorstores, register agents, and prepare retrievers.
    """
    print("🚀 Bootstrapping system...")

    # Load & cache LLMs & embeddings
    get_openai_embeddings()
    get_llm_generic()
    get_llm_generic_with_json()
    get_llm_agent1_dispatch()
    get_llm_agent2_contextualization()
    get_llm_agent2_response()
    get_llm_agent3_followup()

    # Connect to vector databases
    get_weaviate_client()
    get_qdrant_client()
    get_redis_client()

    # Build vectorstore wrapper and retriever
    get_docsearch()
    get_retriever()

    # Ensure agents are registered
    assert agent_registry, "🛑 No agents registered! Did you forget to decorate/register one?"
    print(f"✅ Registered agents: {list(agent_registry.keys())}")

    print("✅ Chatbot system initialized successfully.")
