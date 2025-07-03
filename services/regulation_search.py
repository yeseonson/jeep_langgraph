import json
import time
from jeepchat.logger import logger
from jeepchat.config.config import REGULATION_INDEX_NAME
from jeepchat.services.model_loader import get_embedder
from jeepchat.services.database import opensearch_client

embedder = get_embedder()
#일반 시멘틱 서치
def semantic_search(query_text, top_k=3):
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
        logger.info(f"Executing search query on index '{REGULATION_INDEX_NAME}'...")
        response = client.search(
            body=search_query,
            index=REGULATION_INDEX_NAME
        )
        
        # Process search results
        hits = response['hits']['hits']
        results = []
        
        for hit in hits:
            result = {
                'document': hit['_source'].get('document', '')
            }
            results.append(result)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Semantic search completed: {len(results)} results, time elapsed: {elapsed_time:.2f} seconds")
        logger.info(f"Semantic search results: {results}") # 변경 필요
        return results
        
    except Exception as e:
        logger.error(f"Error during semantic search: {e}", exc_info=True)
        return []
    
# 필터링을 통해 문서 들고오기
def run_filtering_search(filter_dict: dict, top_k=5):
    """
    OpenSearch 필터 기반 검색 함수

    Parameters:
    - filter_dict: 예) { "binary": "구조", "source": "2025 TS자동차튜닝사무편람" }
    - top_k: 반환할 최대 문서 수

    Returns:
    - 검색 결과 리스트 (document만 포함)
    """
    logger.info(f"Starting filtering search: filter={filter_dict}, top_k={top_k}")
    start_time = time.time()

    try:
        client = opensearch_client()

        # filter 리스트 변환
        filter_list = [{ "term": { key: value } } for key, value in filter_dict.items()]
        
        search_query = {
            "size": top_k,
            "query": {
                "bool": {
                    "filter": filter_list
                }
            }
        }

        # logger.debug(f"Filtering search query: {json.dumps(search_query, ensure_ascii=False)}")
        logger.info(f"Executing filtering search on index '{REGULATION_INDEX_NAME}'...")

        response = client.search(index=REGULATION_INDEX_NAME, body=search_query)

        hits = response['hits']['hits']
        results = [{"document": hit['_source'].get('document', '')} for hit in hits]

        elapsed_time = time.time() - start_time
        logger.info(f"Filtering search completed: {len(results)} results, time elapsed: {elapsed_time:.2f} seconds")
        logger.info(f"Filtering search results: {results}")
        return results

    except Exception as e:
        logger.error(f"Error during filtering search: {e}", exc_info=True)
        return []


# 하이브리트 필터링 서치
def hybrid_search_filtering(question, filterring, top_k=5):
    """
    벡터 유사도 + 키워드 매칭 + 필터링이 결합된 하이브리드 검색

    Parameters:
    - question (str): 사용자 질문
    - filterring (dict): 필터링 조건 예시: { "source": ["2025 TS자동차튜닝사무편람"] }
    - top_k (int): 반환할 최대 문서 수

    Returns:
    - List[dict]: 검색 결과 (document만 포함)
    """
    logger.info(f"Starting hybrid filtering search: question='{question}', filter={filterring}, top_k={top_k}")
    start_time = time.time()

    try:
        client = opensearch_client()
        query_embedding = embedder.encode(question)
        logger.debug(f"Query embedding generated (dimensions: {len(query_embedding)})")

        # OpenSearch 쿼리 구성
        search_query = {
            "size": 10,  # top_k보다 크게 설정 후 정렬하여 top_k만 추출
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "multi_match": {
                                        "query": question,
                                        "fields": ["document"],
                                        "fuzziness": "AUTO"
                                    }
                                }
                            ],
                            "filter": [
                                { "terms": filterring }
                            ]
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
                    "boost_mode": "sum"
                }
            }
        }

        # logger.debug(f"Hybrid search query: {json.dumps(search_query, ensure_ascii=False)}")
        logger.info(f"Executing hybrid filtering search on index '{REGULATION_INDEX_NAME}'...")

        response = client.search(index=REGULATION_INDEX_NAME, body=search_query)
        hits = response['hits']['hits']

        if len(hits) > top_k:
            hits = sorted(hits, key=lambda x: x['_score'], reverse=True)[:top_k]

        results = [{"document": hit['_source'].get('document', '')} for hit in hits]

        elapsed_time = time.time() - start_time
        logger.info(f"Hybrid filtering search completed: {len(results)} results in {elapsed_time:.2f} sec")
        logger.info(f"Hybrid filtering search results: {results}")
        return results

    except Exception as e:
        logger.error(f"Error during hybrid filtering search: {e}", exc_info=True)
        return []
