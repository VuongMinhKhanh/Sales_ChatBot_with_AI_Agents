import json

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
import weaviate
from qdrant_client import QdrantClient
from weaviate.classes.init import Auth
from config import REDIS_PASS, REDIS_PORT, REDIS_HOST
import redis

from chatbot.prompts import agent2_response_prompt, \
    agent2_contextualizing_prompt, negativity_avoiding_prompt, information_replacement
from chatbot.vectorstore import retrieve_and_combine_documents, get_retriever
from config import (
    OPENAI_EMBEDDING_MODEL,
    WEAVIATE_CLASS_NAME,
    WEAVIATE_TEXT_KEY,
    OPENAI_API_KEY,
    WEAVIATE_API_KEY,
    WEAVIATE_URL, QDRANT_CLOUD_URL, QDRANT_API_KEY, COLLECTION_NAMES
)

# === Globals (uninitialized) ===
_openai_embeddings = None
_weaviate_client = None
_docsearch = None
_chat_openai_model = None
_llm_generic = None
_llm_generic_with_json = None
_llm_agent1_dispatch = None
_llm_agent2_contextualization = None
_llm_agent2_response = None
_llm_agent3_followup = None
_qdrant_client = None
_rag_chain = None
_contextualized_query = None
_redis_client = None

# === Per-service getter functions ===
def get_qdrant_client():
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(
            url=QDRANT_CLOUD_URL,
            api_key=QDRANT_API_KEY
        )
        print("✅ Initialized Qdrant Client")
    return _qdrant_client

def get_openai_embeddings():
    global _openai_embeddings
    if _openai_embeddings is None:
        _openai_embeddings = OpenAIEmbeddings(
            model=OPENAI_EMBEDDING_MODEL
        )
        print("✅ Initialized OpenAI Embeddings")
    return _openai_embeddings

def get_weaviate_client():
    global _weaviate_client
    if _weaviate_client is None:
        _weaviate_client = weaviate.connect_to_weaviate_cloud(
            cluster_url=WEAVIATE_URL,
            auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
            headers={"X-OpenAI-Api-Key": OPENAI_API_KEY}
        )
        print("✅ Connected to Weaviate Cloud")
    return _weaviate_client


def get_docsearch():
    global _docsearch
    if _docsearch is None:
        from langchain_weaviate.vectorstores import WeaviateVectorStore
        _docsearch = WeaviateVectorStore(
            client=get_weaviate_client(),
            index_name=WEAVIATE_CLASS_NAME,
            text_key=WEAVIATE_TEXT_KEY,
            embedding=get_openai_embeddings()
        )
        print("✅ Initialized Docsearch (Vectorstore)")
    return _docsearch


def get_llm_generic():
    global _llm_generic
    if _llm_generic is None:
        _llm_generic = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )
        print("✅ Initialized LLM Generic")
    return _llm_generic


def get_llm_generic_with_json():
    global _llm_generic_with_json
    if _llm_generic_with_json is None:
        _llm_generic_with_json = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            model_kwargs={
                "response_format": {"type": "json_object"}
            }
        )
        print("✅ Initialized LLM Generic (JSON enforced)")
    return _llm_generic_with_json


def get_llm_agent1_dispatch():
    global _llm_agent1_dispatch
    if _llm_agent1_dispatch is None:
        _llm_agent1_dispatch = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.5,
            streaming=True,
            model_kwargs={
                "response_format": {"type": "json_object"}
            }
        )
        print("✅ Initialized Agent1 Dispatcher Model (JSON enforced)")
    return _llm_agent1_dispatch


def get_llm_agent2_contextualization():
    global _llm_agent2_contextualization
    if _llm_agent2_contextualization is None:
        _llm_agent2_contextualization = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            streaming=False,
            model_kwargs={
                "response_format": {"type": "json_object"}
            }
        )
        print("✅ Initialized Agent2 Contextualization Model (JSON enforced)")
    return _llm_agent2_contextualization


def get_llm_agent2_response():
    global _llm_agent2_response
    if _llm_agent2_response is None:
        _llm_agent2_response = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            streaming=False,
        )
        print("✅ Initialized Agent2 Response Model (JSON enforced)")
    return _llm_agent2_response


def get_llm_agent3_followup():
    global _llm_agent3_followup
    if _llm_agent3_followup is None:
        _llm_agent3_followup = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            streaming=False,
            model_kwargs={
                "response_format": {"type": "json_object"}
            }
        )
        print("✅ Initialized Agent3 Followup Model (JSON enforced)")
    return _llm_agent3_followup


def initialize_rag():
    global _rag_chain
    if _rag_chain is None:
        def wrapped_retriever(input_data):
            input_query = input_data.content
            # print("input_query:", input_query)
            input_query = json.loads(input_query)
            primary_query = input_query["primary"]
            secondary_query = input_query["secondary"]
            full_contextualized_query = input_query["full_contextualized_query"]

            global _contextualized_query
            _contextualized_query = full_contextualized_query

            return retrieve_and_combine_documents(
                primary_query,
                secondary_query,
                get_retriever(),
                get_docsearch(),
                WEAVIATE_CLASS_NAME
            )

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", agent2_contextualizing_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                ("ai", "📊 Nghiệp vụ doanh nghiệp: {business_logic}"),
                ("ai", "📊 Phản hồi người dùng: {user_feedback}"),
                ("ai", "🧑‍💼 Mô tả khách hàng: {user_profile}")
            ]
        )

        # Create a history-aware retriever using the custom wrapped retriever
        history_aware_retriever = contextualize_q_prompt | get_llm_agent2_contextualization() | wrapped_retriever

        # retrieved_chunks = history_aware_retriever.invoke(test_input)
        # print("retrieved_chunks:", retrieved_chunks)
        qa_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", agent2_response_prompt +  "\n\n" +
                     information_replacement + "\n\n" +
                    #  + feedback_content +    "\n\n"
                     negativity_avoiding_prompt + "\n\n"
                    # + contextualized_query_usage + "\n\n"
                    #  "Context: \n" + "{context}"
                     ),
                    MessagesPlaceholder("chat_history"),
                    ("ai", "Context: \n{context}"),
                    ("human", "User message: {input}"),
                    # ("ai", "Contextualized query: {contextualized_query}"),
                    ("ai", "User profile: {user_profile}"),
                    ("ai", "Business Logic to follow:\n{business_logic}"),
                    ("ai", "Current Workflow Stage: {workflow_stage}"),
                    ("ai", "Workflow Instruction:\n{instruction}"),
                    ("ai", "User Feedback:\n{user_feedback}"),
                    ("ai", "This is a hint for your response:\n{agent2_hint}")
                ]
            )

        # Initialize memory and QA system
        question_answer_chain = create_stuff_documents_chain(get_llm_agent2_response(), qa_prompt)

        # Create and return the RAG chain
        _rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return _rag_chain


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(host=REDIS_HOST,
                                          password=REDIS_PASS,
                                          port=REDIS_PORT, db=0)
        print("✅ Connected to Redis")
    return _redis_client
