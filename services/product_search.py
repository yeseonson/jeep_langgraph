# -*- coding: utf-8 -*-
import time
import json
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
            "데루등": "Tail Lamp"
        }

    def replace_keywords(self, keywords: List[str]) -> List[str]:
        """추출된 키워드를 상품명 검색에 적합한 대체 키워드로 변환"""
        replaced_keywords = []
        original_keywords = set(keywords)  # 원본 키워드 유지
        
        for keyword in keywords:
            replaced_keywords.append(keyword)  # 원본 키워드 유지
            
            # 키워드 대체 사전에 있는 경우 대체 키워드 추가
            if keyword in self.keyword_replacements:
                replacement = self.keyword_replacements[keyword]
                replaced_keywords.append(replacement)
                logger.debug(f"Keyword replacement: '{keyword}' -> '{replacement}'")
        
        # 중복 제거 및 로깅
        replaced_unique = list(dict.fromkeys(replaced_keywords))
        
        # 추가된 대체 키워드 로깅
        added_keywords = set(replaced_unique) - original_keywords
        if added_keywords:
            logger.debug(f"Added replacement keywords: {added_keywords}")
        
        return replaced_unique 
    
    def build_query_body(self, processed_query, query_vector, size: int = PRODUCT_TOP_K, vehicle_fitment=None):
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
                                        "minimum_should_match": "5%"
                                    }
                                }
                            },
                            {
                                "match": {
                                    "product_name": {
                                        "query": processed_query,
                                        "boost": 1,
                                        "minimum_should_match": "5%"
                                    }
                                }
                            },
                            {
                                "match": {
                                    "keywords": {
                                        "query": processed_query,
                                        "boost": 2,
                                        "minimum_should_match": "5%"
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
            bool_query["filter"] = [
                {
                    "match_phrase": {
                        "vehicle_fitment": vehicle_fitment
                    }
                }
            ]

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
        """사용자 쿼리를 분석하여 검색 쿼리 생성"""
        try:
            # 키워드 대체
            keywords = query_text.split()
            replaced_keywords = self.replace_keywords(keywords)
            processed_query = " ".join(replaced_keywords)

            logger.debug(f"Original query: {query_text}")
            logger.debug(f"Replaced query: {processed_query}")

            query_vector = self.embedder.encode(processed_query, batch_size=8).tolist()
            query_body = self.build_query_body(processed_query, query_vector, size, vehicle_fitment)

            text_query = query_body.get('query', {}).get('function_score', {}).get('query', {})

            logger.debug(f"Opensearch query: {json.dumps(text_query, ensure_ascii=False)}")
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