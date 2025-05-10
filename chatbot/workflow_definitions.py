def get_workflow_stages():
    """Trả về định nghĩa quy trình bán hàng."""
    workflow_data = {
        "Greeting": {
            "internal_instruction": "Chào hỏi khách hàng thân thiện, giới thiệu dịch vụ/sản phẩm...",
            "sample_user_query": [...],
            "sample_response": "...",
            "identify": "...",
        },
        "Needs Assessment": {
            "internal_instruction": "Đặt câu hỏi trọng tâm để khám phá nhu cầu...",
            "sample_user_query": [...],
            "sample_response": "...",
            "identify": "...",
        },
        # More stages here...
    }
    return workflow_data

def get_workflow(current_stage):
    workflow_data = get_workflow_stages()
    return workflow_data.get(current_stage, {}).get("internal_instruction", None)

def get_workflow_identify() -> dict:
    """Trả về {stage: {"identify": ..., "sample_user_query": [...]}}."""
    workflow_data = get_workflow_stages()
    return {
        stage: {
            "identify": info["identify"],
            "sample_user_query": info.get("sample_user_query", [])
        }
        for stage, info in workflow_data.items()
    }

def get_workflow_instruction() -> dict:
    """Trả về {stage: {"internal_instruction": ...,}}."""
    workflow_data = get_workflow_stages()
    return {
        stage: {
            "internal_instruction": info["internal_instruction"],
        }
        for stage, info in workflow_data.items()
    }
