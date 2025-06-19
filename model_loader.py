
from config import OPENAI_CLIENT, GPT_4O_MINI_MODEL_ID, QWEN3_4B_MODEL_ID, HYPERCLOVA_3B_MODEL_ID
from openai import OpenAI
from sentence_transformers import SentenceTransformer

def hyperclova_response(system_prompt, user_input):
    client = OpenAI(api_key="EMPTY",
                    base_url="http://localhost:8000/v1"
            )

    response = client.chat.completions.create(
        model=str(HYPERCLOVA_3B_MODEL_ID),
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.7,
        top_p=0.8,
        presence_penalty=1.5,
        extra_body={
            "top_k": 20, 
            "chat_template_kwargs": {"enable_thinking": False}
        }
    )
    
    return str(response.choices[0].message.content).strip()

# --- OpenAI GPT-4o mini 설정 ---
def openai_response(system_prompt, user_input, temperature=0.3, max_tokens=512):
    """OpenAI API를 호출하여 사용자 입력에 대한 응답 생성"""

    response = OPENAI_CLIENT.chat.completions.create(
        model=str(GPT_4O_MINI_MODEL_ID),
        messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            
    )
    return str(response.choices[0].message.content).strip()

# --- Qwen3-4B 설정 ---
def qwen_response(system_prompt, user_input):
    client = OpenAI(api_key="EMPTY",
                    base_url="http://localhost:8000/v1",
                )
    response = client.chat.completions.create(
        model=str(QWEN3_4B_MODEL_ID),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        
        max_tokens=512
    )
    return str(response.choices[0].message.content).strip()

# --- 임베딩 모델 ---
def get_embedder():
    """임베딩 모델을 반환"""
    return SentenceTransformer("BAAI/bge-m3")