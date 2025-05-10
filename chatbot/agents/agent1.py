import json, time
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from chatbot.prompts import agent1_prompt
from chatbot.vectorstore import retrieve_context_sync
from chatbot.workflow_definitions import get_workflow_identify
from services import get_llm_agent1_dispatch


def agent1_dispatch_agents(chat_history,
                            predicted_stage: str,
                            user_profile: str,
                            user_query: str,
                            workflow_identify: str = None,
                            top_k=3):
    """
    Chạy Agent 1:
    - Gọi LLM sinh JSON kết quả
    - Truy vấn context bổ sung
    - Trả về JSON hoàn chỉnh
    """

    if workflow_identify is None:
        "Greeting, Needs Assessment, Qualification, Presentation, Objection Handling, Closing, Follow-Up"

    workflow_identify = get_workflow_identify()
    workflow_identify = "\n".join([
        f"- {stage}: {info['identify']}"
        for stage, info in workflow_identify.items()
    ])

    # 1. Build prompt
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", agent1_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "User Message: {user_query}"),
        ("human", "Customer Profile: {user_profile}"),
        ("ai", "Workflow Stages: {workflow_identify}"),
        ("ai", "Predicted Stage: {predicted_stage}"),
    ])

    # 2. Create LLM instance
    llm_agent1_dispatch = get_llm_agent1_dispatch()

    chain = prompt_template | llm_agent1_dispatch

    # 3. Invoke LLM
    start = time.time()
    response_text = chain.invoke({
        "user_query": user_query,
        "predicted_stage": predicted_stage,
        "user_profile": user_profile,
        "chat_history": chat_history,
        "workflow_identify": workflow_identify
    })

    # print("response_text:", response_text)

    # 4. Parse JSON
    parsed_json = json.loads(response_text.content)
    # print("parsed_json", parsed_json)

    # 5. Đồng bộ truy vấn retrieval context
    semantic_query = parsed_json.get('query_and_stage', {}).get('semantic_query')
    workflow_stage = parsed_json.get('query_and_stage', {}).get('workflow_stage')
    retrieval_context = retrieve_context_sync(semantic_query, workflow_stage, top_k)

    # 6. Gắn thêm vào kết quả
    parsed_json['retrieval_context'] = retrieval_context

    end = time.time()
    print(f"⏱️ Time taken Agent 1: {end - start:.4f}s")
    return parsed_json, float(f"{end - start:.4f}")