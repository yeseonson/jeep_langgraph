# -*- coding: utf-8 -*-
import time
import json
from typing import Dict, Any, List
from jeepchat.logger import logger
from jeepchat.services.database import opensearch_client
from jeepchat.services.model_loader import get_embedder
from jeepchat.config.config import PRODUCT_INDEX_NAME
from jeepchat.config.constants import PRODUCT_TOP_K

class JeepSearchServiceKW:
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
        # 주요 부품 키워드 부스팅
        self.part_keywords = [
            "휠",
            "라이트바", "하드탑", "소프트탑", "쇼바", "휀더", "범퍼", "루프랙", "스텝바",  "타이어",
            "스키드플레이트", "윈드쉴드", "휠하우스", "서스펜션", "브레이크",
        ]

    def replace_keywords(self, keywords: List[str]) -> List[str]:
        """추출된 키워드를 상품명 검색에 적합한 대체 키워드 추가"""
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

    def _build_keyword_match_functions(self, query_text: str) -> List[Dict[str, Any]]:
        """질문에 포함된 부품 키워드에 match_phrase 기반 가중치 부여"""
        matched_keywords = [kw for kw in self.part_keywords if kw in query_text]
        return [
            {
                "filter": {
                    "match_phrase": {
                        "product_name_ko": kw
                    }
                },
                "weight": 70
            } for kw in matched_keywords
        ]

    def build_query_body(self, query_text, processed_query, query_vector, size: int = PRODUCT_TOP_K, vehicle_fitment=None):
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
                            }
                        ]
                    }
                }
            ]
        }

        # vehicle_fitment 필터링
        if vehicle_fitment:
            bool_query["filter"] = [
                {
                    "match_phrase": {
                        "vehicle_fitment": vehicle_fitment
                    }
                }
            ]

        # 🔧 주요 부품 키워드가 쿼리에 포함되어 있으면 should 쿼리에 추가
        matched_keywords = [kw for kw in self.part_keywords if kw in query_text]
        for kw in matched_keywords:
            bool_query["should"].append({
                "match": {
                    "product_name_ko": {
                        "query": kw,
                        "boost": 2  # 높은 boost로 중요도 강조
                    }
                }
            })

        # 부품 키워드에 대한 가중치 조정 (function_score.functions에 포함)
        keyword_match_functions = [
            {
                "filter": {
                    "match": {
                        "product_name_ko": kw
                    }
                },
                "weight": 70
            } for kw in matched_keywords
        ]

        # 최종 쿼리 바디
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
                    ] + keyword_match_functions,
                    "boost_mode": "multiply",
                    "score_mode": "max"
                }
            }
        }

        return query_body

    def search(self, query_text: str, size: int = PRODUCT_TOP_K, vehicle_fitment=None) -> List[Dict[str, Any]]:
        
        logger.info(f"Starting keyword boosted search: '{query_text}', top_k={size}")

        # 키워드 대체
        keywords = query_text.split()
        replaced_keywords = self.replace_keywords(keywords)
        processed_query = " ".join(replaced_keywords)

        logger.info(f"Original query: {query_text}")
        logger.info(f"Replaced query: {processed_query}")

        # 쿼리 벡터 생성
        query_vector = self.embedder.encode(processed_query).tolist()

        # 쿼리 바디 구성
        query_body = self.build_query_body(query_text, processed_query, query_vector, size, vehicle_fitment)

        logger.debug(f"Opensearch query: {json.dumps(query_body, ensure_ascii=False)}")

        # 검색 수행
        start_time = time.time()
        response = self.client.search(index=self.index_name, body=query_body)
        hits = response["hits"]["hits"]
        elapsed_time = time.time() - start_time
        logger.info(f"Search completed: {len(hits)} results, time elapsed: {elapsed_time:.2f} seconds")

        # 결과 정제
        result = [
            {
                "model_no": hit["_source"].get("model_no", ""),
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

        return result

# 예시 실행
if __name__ == "__main__":
    search_service = JeepSearchServiceKW()
    results = search_service.search("JL로 도하 주행시 쓸 수 있는 호환성 좋은 스노클 모델 추천 부탁해", size=PRODUCT_TOP_K, vehicle_fitment=None)

    for r in results:
        logger.info(f"{r}")
        print(r)
