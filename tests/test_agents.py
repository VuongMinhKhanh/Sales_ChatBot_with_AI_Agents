from chatbot.agents.agent2 import agent2_retrieve_product_info
from services import initialize_rag, get_llm_agent2_contextualization



#%% test rag
print(get_llm_agent2_contextualization())

rag = initialize_rag()

print("rag", rag)

#%% test agent 2



