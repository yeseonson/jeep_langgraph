# -*- coding: utf-8 -*-
import time
# import json
from typing import Dict, Any, List
from jeepchat.logger import logger
from jeepchat.services.database import opensearch_client
from jeepchat.services.model_loader import get_embedder
from jeepchat.config.config import PRODUCT_INDEX_NAME
from jeepchat.config.constants import PRODUCT_TOP_K

class JeepSearchService:
    def __init__(self):
        self.client = opensearch_client()
        self.index_name = PRODUCT_INDEX_NAME
        self.embedder = get_embedder()
        # 키워드 대체 사전
        self.keyword_replacements = {
            "쇼바": "Shock Absorber",
            "휀더": "Fender",
            "휀다": "Fender",
            "암대": "Long Arm",
            "8암대": "8 inch Long Arm",
            "데후": "Differential Gear",
            "데루등": "Tail Lamp",
            "단통": "Monotube",
            "루프랙": "Roof Rack",
            "휠": "Wheel",
            "타이어": "Tire",
            "브레이크": "Brake",
            "서스펜션": "Suspension",
            "휠하우스": "Wheel House",
            "범퍼": "Bumper",
            "스텝바": "Step Bar",
            "스키드플레이트": "Skid Plate",
            "윈드쉴드": "Windshield",
            "스노클": "Snorkel",
            "라이트바": "Light Bar", 
            "하드탑": "Hard Top", 
            "소프트탑": "Soft Top", 
        }

    def replace_keywords(self, query_text: str) -> str:
        """질문 내에 부품 키워드가 포함되어 있으면 대체 키워드를 함께 추가"""
        replacements = []

        for keyword, replacement in self.keyword_replacements.items():
            if keyword in query_text:
                replacements.append(replacement)
                logger.debug(f"'{keyword}' found in query_text → '{replacement}' added")

        # 최종 검색어는 원문 + 추가 키워드
        extended_query = f"{query_text} {' '.join(replacements)}" if replacements else query_text
        return extended_query
    
    def build_query_body(self, processed_query, query_vector, size: int = PRODUCT_TOP_K, vehicle_fitment=None):
        """사용자 쿼리를 분석하여 검색 쿼리 생성"""
        bool_query = {
            "should": [
                {
                    "dis_max": {
                        "queries": [
                            {
                                "match": {
                                    "product_name_ko": {
                                        "query": processed_query,
                                        "boost": 1,
                                        "minimum_should_match": "1"
                                    }
                                }
                            },
                            {
                                "match": {
                                    "product_name": {
                                        "query": processed_query,
                                        "boost": 1,
                                        "minimum_should_match": "1"
                                    }
                                }
                            },
                            {
                                "match": {
                                    "keywords": {
                                        "query": processed_query,
                                        "boost": 2,
                                        "minimum_should_match": "1"
                                    }
                                }
                            },
                        ]
                    }
                }
            ]
        }

        # vehicle_fitment 값이 주어진 경우 filter 조건 추가
        if vehicle_fitment:
            bool_query.setdefault("filter", [])
            
            bool_query["should"].append({
                "match_phrase": {
                    "vehicle_fitment": vehicle_fitment
                }
            })
            bool_query["should"].append({
                "term": {
                    "vehicle_fitment.keyword": "all"
                }
            })

        query_body = {
            "size": size,
            "query": {
                "function_score": {
                    "query": {
                        "bool": bool_query
                    },
                    "functions": [
                        {
                            "script_score": {
                                "script": {
                                    "source": "knn_score",
                                    "lang": "knn",
                                    "params": {
                                        "field": "embedding_vector",
                                        "query_value": query_vector,
                                        "space_type": "cosinesimil"
                                    }
                                }
                            },
                            "weight": 50
                        }
                    ],
                    "boost_mode": "multiply",
                    "score_mode": "max"
                }
            }
        }

        return query_body

    def search(self, query_text: str, size: int = PRODUCT_TOP_K, vehicle_fitment=None) -> List[Dict[str, Any]]:
        """오픈서치 상품검색 실행"""
        try:
            if vehicle_fitment:
                logger.info(f"Starting product search: '{query_text}', top_k={size}, vehicle_fitment='{vehicle_fitment}'")
            else:
                logger.info(f"Starting product search: '{query_text}', top_k={size}")
                
            # 키워드 대체
            processed_query = self.replace_keywords(query_text)

            logger.debug(f"Original query: {query_text}")
            logger.info(f"Processed query: {processed_query}")

            query_vector = self.embedder.encode(processed_query, batch_size=8).tolist()
            query_body = self.build_query_body(processed_query, query_vector, size, vehicle_fitment)

            text_query = query_body.get('query', {}).get('function_score', {}).get('query', {})

            #logger.debug(f"Opensearch query: {json.dumps(text_query, ensure_ascii=False)}")
            logger.debug(f"Search size: {query_body.get('size', 'default')}")

            start_time = time.time()
            response = self.client.search(index=self.index_name, body=query_body)
            hits = response["hits"]["hits"]
            elapsed_time = time.time() - start_time
            logger.debug(f"Search completed: {len(hits)} results, time elapsed: {elapsed_time:.2f} seconds")
            
            result = [
                {   "model_no": hit["_source"].get("model_no", ""),
                    "product_name_ko": hit["_source"].get("product_name_ko", ""),
                    "score": hit["_score"],
                    "product_name": hit["_source"].get("product_name", ""),
                    "manufacturer": hit["_source"].get("manufacturer", ""),
                    "price": hit["_source"].get("price", ""),
                    "main_category": hit["_source"].get("main_category"),
                    "product_url": hit["_source"].get("detail_url")
                }
                for hit in hits
            ]
            
            # model_no_list = [item["model_no"] for item in result if item["model_no"]]
            
            return result

        except Exception as e:
            logger.error(f"Error during search processing: {str(e)}", exc_info=True)
            raise


# 예시 실행
if __name__ == "__main__":
    search_service = JeepSearchService()
    results = search_service.search("글래디에이터 타이어", size=PRODUCT_TOP_K)
    print(results)