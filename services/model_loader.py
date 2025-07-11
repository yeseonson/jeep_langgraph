
import os
from jeepchat.config.config import OPENAI_CLIENT, GPT_4O_MINI_MODEL_ID, QWEN3_4B_MODEL_ID, HYPERCLOVA_3B_MODEL_ID, HF_HOME
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from jeepchat.logger import logger

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
def openai_response(system_prompt, user_input, model_id=GPT_4O_MINI_MODEL_ID, temperature=0.3, max_tokens=1024):
    """OpenAI API를 호출하여 사용자 입력에 대한 응답 생성"""
    response = OPENAI_CLIENT.chat.completions.create(
        model=model_id,
        messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            
    )
    usage = response.usage
    logger.debug(f"[OPENAI CALL] model={model_id}, prompt_len={len(system_prompt)}, user_input_len={len(user_input)}, usage={usage}")
    
    return str(response.choices[0].message.content).strip()

def openai_response_with_function(system_prompt, user_input, functions, function_call):
    response = OPENAI_CLIENT.chat.completions.create(
        model=str(GPT_4O_MINI_MODEL_ID),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        functions=functions,
        function_call=function_call,
    )
    return response.choices[0].message.function_call.arguments

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
_embedder_cache = None

def get_embedder():
    """임베딩 모델을 반환 (싱글톤 패턴)"""
    global _embedder_cache
    if _embedder_cache is None:
        logger.info("Loading embedding model for the first time...")
        _embedder_cache = SentenceTransformer("BAAI/bge-m3")
        logger.info("Embedding model loaded successfully")
    return _embedder_cache