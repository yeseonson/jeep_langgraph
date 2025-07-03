from pydantic import BaseModel, Field
from jeepchat.services.model_loader import openai_response, openai_response_with_function
from jeepchat.config.prompts import generate_prompt, re_write_prompt, retrieval_grader_prompt
import json

TOP_K = 5

# 검색된 문서의 관련성 여부를 이진 점수로 평가하는 데이터 모델
class GradeDocuments(BaseModel):
    """A binary score to determine the relevance of the retrieved document."""

    # 문서가 질문과 관련이 있는지 여부를 'yes' 또는 'no'로 나타내는 필드
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )

def get_grade_documents_schema():
    props = GradeDocuments.schema()["properties"]
    required = GradeDocuments.schema().get("required", [])
    return {
        "name": "GradeDocuments",
        "description": GradeDocuments.__doc__ or "",
        "parameters": {
            "type": "object",
            "properties": props,
            "required": required
        }
    }

def retrieval_grader(user_input: str, documents: str) -> GradeDocuments:
    schema = get_grade_documents_schema()
    system_prompt, user_prompt = retrieval_grader_prompt(user_input, documents)
    
    args = openai_response_with_function(
        system_prompt=system_prompt,
        user_input=user_prompt,
        functions=[schema],
        function_call={"name": "GradeDocuments"},
    )
    
    data = json.loads(args)
    is_relevant = GradeDocuments(**data)
    
    return is_relevant

def generate_answer(user_input: str, documents: str) -> str:
    # 프롬프트 생성
    system_prompt, user_prompt = generate_prompt(user_input, documents)
    
    answer = openai_response(
        system_prompt=system_prompt,
        user_input=user_prompt
    )
    return answer

def question_rewriter(user_input: str) -> str:
    # 프롬프트(시스템 컨텍스트) 생성
    system_prompt, user_prompt = re_write_prompt(user_input)
    
    rewritten = openai_response(
        system_prompt=system_prompt,
        user_input=user_prompt
    )
    return rewritten