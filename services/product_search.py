# -*- coding: utf-8 -*-
import time
# import json
from typing import Dict, Any, List
from jeepchat.logger import logger
from jeepchat.services.database import opensearch_client
from jeepchat.services.model_loader import get_embedder
from jeepchat.config.config import PRODUCT_INDEX_NAME
from jeepchat.config.constants import PRODUCT_TOP_K
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class JeepSearchService:
    def __init__(self):
        self.client = opensearch_client()
        self.index_name = PRODUCT_INDEX_NAME
        self.stop_words = set(stopwords.words("english"))
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
            "리프트킷": "Lift Kit",
            "윈치": "Winch",
            "루프랙": "Roof Rack",
            "베드랙": "Bed Rack",
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
            "소탑": "Soft Top",
        }

    def replace_keywords(self, query_text: str) -> str:
        replacements = []

        # 소문자 기준 비교용 (영어 질의 대비)
        lowered_query = query_text.lower()

        for keyword_kr, keyword_en in self.keyword_replacements.items():
            # 한국어 키워드 포함 여부
            if keyword_kr in query_text:
                replacements.append(keyword_en)
                logger.debug(f"[KR] '{keyword_kr}' found in query_text → '{keyword_en}' added")
            # 영어 키워드 포함 여부 (단어 단위가 아니더라도 부분 일치 시 추가 가능)
            elif keyword_en.lower() in lowered_query:
                if keyword_en not in replacements:
                    replacements.append(keyword_en)
                    logger.debug(f"[EN] '{keyword_en}' found in query_text → '{keyword_en}' retained")

        # 최종 검색어 확장
        extended_query = f"{query_text} {' '.join(replacements)}" if replacements else query_text
        return extended_query
    
    def contains_korean(self, text: str) -> bool:
        return any('\uac00' <= char <= '\ud7a3' for char in text)

    def clean_english(self, text: str, max_tokens: int = 50) -> str:
        tokens = word_tokenize(text)
        filtered = [t for t in tokens if t.lower() not in self.stop_words and t.isalnum()]
        return ' '.join(filtered[:max_tokens])

    def build_query_body(self, processed_query, query_vector, size: int = PRODUCT_TOP_K, vehicle_fitment=None):
        is_korean = self.contains_korean(processed_query)

        if is_korean:
            # 한국어 쿼리 구성
            match_query = {
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
        else:
            # 영어 전처리
            processed_query = self.clean_english(processed_query)

            # 영어 쿼리 구성
            match_query = {
                "multi_match": {
                    "query": processed_query,
                    "type": "most_fields",
                    "fields": [
                       "product_name^3",
                        "product_name_ko^1",
                        "keywords^2"
                    ],
                    "minimum_should_match": "1"
                }
            }

        # bool 쿼리 구성
        bool_query = {
            "should": [match_query]
        }

        # vehicle_fitment 필터링
        if vehicle_fitment:
            bool_query["filter"] = [
                {
                    "bool": {
                        "should": [
                            {
                                "match_phrase": {
                                    "vehicle_fitment": vehicle_fitment
                                }
                            },
                            {
                                "match": {
                                    "vehicle_fitment": "all"
                                }
                            }
                        ],
                        "minimum_should_match": 1
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
                    "product_url": hit["_source"].get("detail_url"),
                    "features_details": hit["_source"].get("features_details", ""),
                    "specifications": hit["_source"].get("specifications", ""),
                    "included_in_price": hit["_source"].get("included_in_price", ""),
                }
                for hit in hits
            ]
            
            return result

        except Exception as e:
            logger.error(f"Error during search processing: {str(e)}", exc_info=True)
            raise

# 예시 실행
if __name__ == "__main__":
    search_service = JeepSearchService()
    results = search_service.search("지프 글래디에이터 4.5 인치 리프트킷을 추천해주세요", size=PRODUCT_TOP_K)
    print(results)