import json
import time
from jeepchat.config.config import KNOWLEDGE_INDEX_NAME
from jeepchat.logger import logger
from jeepchat.services.database import opensearch_client
from jeepchat.services.model_loader import get_embedder
from dotenv import load_dotenv
load_dotenv()

TOP_K = 5 
embedder = get_embedder()

def semantic_search(query_text, top_k=TOP_K):
    logger.info(f"Starting semantic search: '{query_text}', top_k={top_k}")
    start_time = time.time()
    
    try:
        client = opensearch_client()
        
        query_embedding = embedder.encode(query_text)
        logger.debug(f"Query embedding generated (dimensions: {len(query_embedding)})")
        
        search_query = {
            "size": top_k,
            "query": {
                "knn": {
                    "embedding_vector": {
                        "vector": query_embedding.tolist(),
                        "k": top_k
                    }
                }
            }
        }
        
        # Execute search
        logger.info(f"Executing search query on index '{KNOWLEDGE_INDEX_NAME}'...")
        response = client.search(
            body=search_query,
            index=KNOWLEDGE_INDEX_NAME
        )
        
        # Process search results
        hits = response['hits']['hits']
        results = []
        
        for hit in hits:
            result = {
                'score': hit['_score'],
                'document': hit['_source'].get('document', ''),
            }
            results.append(result)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Semantic search completed: {len(results)} results, time elapsed: {elapsed_time:.2f} seconds")
        logger.info(f"Semantic search results: {print_search_results(results=results, query=query_text)}")
        return results
        
    except Exception as e:
        logger.error(f"Error during semantic search: {e}", exc_info=True)
        return []

def hybrid_search(query_text, top_k=TOP_K):
    logger.info(f"Starting hybrid search: '{query_text}', top_k={top_k}")
    start_time = time.time()
    
    try:
        client = opensearch_client()
        
        query_embedding = embedder.encode(query_text)
        logger.debug(f"Query embedding generated (dimensions: {len(query_embedding)})")
        
        # Hybrid search query (keyword search + KNN search)
        search_query = {
            "size": top_k,
            "query": {
                "function_score": {
                    "query": {
                        "multi_match": {
                            "query": query_text,
                            "fields": ["document"],
                            "fuzziness": "AUTO"
                        }
                    },
                    "functions": [
                        {
                            "script_score": {
                                "script": {
                                    "source": "knn_score",
                                    "lang": "knn",
                                    "params": {
                                        "field": "embedding_vector",
                                        "query_value": query_embedding.tolist(),
                                        "space_type": "cosinesimil"
                                    }
                                }
                            },
                            "weight": 50
                        }
                    ],
                    "score_mode": "sum",
                    "boost_mode": "multiply"
                }
            }
        }
        
        logger.debug(f"Search size: {search_query.get('size', 'default')}")
        
        # Execute search
        logger.info(f"Executing hybrid search query on index '{KNOWLEDGE_INDEX_NAME}'...")
        response = client.search(
            body=search_query,
            index=KNOWLEDGE_INDEX_NAME
        )
        
        # Process search results
        hits = response['hits']['hits']
        results = []
        
        for hit in hits:
            result = {
                'score': hit['_score'],
                'document': hit['_source'].get('document', ''),
            }
            results.append(result)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Hybrid search completed: {len(results)} results, time elapsed: {elapsed_time:.2f} seconds")
        logger.info(f"Hybrid search results: {print_search_results(results=results, query=query_text)}")
        return results
        
    except Exception as e:
        logger.error(f"Error during hybrid search: {e}", exc_info=True)
        return []

# 결과 출력
def print_search_results(results, query):
    header = f"=== '{query}' 검색 결과 ({len(results)}건) ==="
    print(header)
    logger.info(header)

    for i, result in enumerate(results):
        logger.info(f"[{i+1}] 점수: {result['score']:.4f}")
        logger.info(result["document"])


def main():
    test_queries = [
        "겨울철 눈길 운전할 때 좋은 루비콘 타이어 알려줘",
      #  "지프 타이어 교체",
      #  "연비 개선 방법",
      #  "승차감 향상 부품"
    ]
    
    print("=== 벡터 검색(시맨틱 검색) 테스트 ===")
    logger.info("Starting vector search (semantic search) tests")
    for query in test_queries:
        results = semantic_search(query)
        print_search_results(results, query)
    logger.info("Vector search (semantic search) tests completed")
    
    print("=== 하이브리드 검색(키워드 + 시맨틱) 테스트 ===")
    logger.info("Starting hybrid search (keyword + semantic) tests")
    for query in test_queries:
        results = hybrid_search(query)
        print_search_results(results, query)
    logger.info("Hybrid search (keyword + semantic) tests completed")
    
    # 대화형 검색 모드
    print("=== 대화형 검색 모드 ===")
    logger.info("Starting interactive search mode")
    print("검색어를 입력하세요. 종료하려면 'q' 또는 'exit'를 입력하세요.")
    
    while True:
        query = input("\n검색어: ")
        if query.lower() in ['q', 'exit', '종료']:
            logger.info("User requested to exit the program")
            break
            
        search_type = input("검색 유형 (1: 벡터 검색, 2: 하이브리드 검색): ")
        logger.info(f"User input - Query: '{query}', Search type: {search_type}")
        
        if search_type == '1':
            logger.info("Executing vector search")
            results = semantic_search(query)
            print_search_results(results, query)
        elif search_type == '2':
            logger.info("Executing hybrid search")
            results = hybrid_search(query)
            print_search_results(results, query)
        else:
            logger.warning(f"Invalid search type input: {search_type}")
            print("잘못된 검색 유형입니다. 1 또는 2를 입력하세요.")
    
    logger.info("Program terminated")

if __name__ == "__main__":
    try:
        logger.info(f"System configuration - Index: {KNOWLEDGE_INDEX_NAME}, TOP_K: {TOP_K}")
        main()
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        print(f"오류가 발생했습니다: {e}")