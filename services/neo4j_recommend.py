import os
import time
from dotenv import load_dotenv
from jeepchat.config.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from jeepchat.logger import logger
from typing import List, Dict, Any
from langchain_neo4j import Neo4jGraph

load_dotenv()

def recommend_parts(graph: Neo4jGraph, input_model_nos: List[str], optional_query: str) -> Dict[str, Dict[str, Any]]:
    start_time = time.time()
    logger.info(f"부품 추천 시작 - 입력 부품 수: {len(input_model_nos)}, 부품 목록: {input_model_nos}")
    
    if not isinstance(optional_query, str):
        optional_query = ""

    query = ("""
             MATCH (basePart:Part {model_no: $input_model_no})
            OPTIONAL MATCH (basePart)-[:MANUFACTURED_BY]->(baseManufacturer:Manufacturer)
            OPTIONAL MATCH (basePart)-[:BELONGS_TO]->(category:Category)

            // 기준 부품의 차종 정보
            OPTIONAL MATCH (basePart)-[:FITS_FOR]->(v1:Vehicle)
            OPTIONAL MATCH (basePart)-[:FITS_FOR]->(:UniversalVehicle {type: 'all'})-[:COVERS]->(v2:Vehicle)

            WITH basePart, baseManufacturer, category,
                COLLECT(DISTINCT v1) + COLLECT(DISTINCT v2) AS baseVehicles,
                EXISTS((basePart)-[:FITS_FOR]->(:UniversalVehicle {type: 'all'})) AS isUniversalBase

            // 추천 부품 조회 (선택적)
            OPTIONAL MATCH (category)<-[:BELONGS_TO]-(recommendPart:Part)-[:MANUFACTURED_BY]->(recManufacturer:Manufacturer)
            WHERE recommendPart.model_no <> basePart.model_no
            """
            + optional_query +
            """
            //AND recommendPart.price >= basePart.price * 0.8 //비슷한 가격대 추천
            //AND recommendPart.price <= basePart.price * 1.2

            // 추천 부품의 차종 정보
            OPTIONAL MATCH (recommendPart)-[:FITS_FOR]->(cv1:Vehicle)
            OPTIONAL MATCH (recommendPart)-[:FITS_FOR]->(:UniversalVehicle {type: 'all'})-[:COVERS]->(cv2:Vehicle)

            WITH basePart, baseManufacturer, category, baseVehicles, isUniversalBase,
                recommendPart, recManufacturer,
                COLLECT(DISTINCT cv1) + COLLECT(DISTINCT cv2) AS recVehicles,
                EXISTS((recommendPart)-[:FITS_FOR]->(:UniversalVehicle {type: 'all'})) AS isUniversalRec

            // 차종 호환성 체크 및 추천 부품 필터링
            WITH basePart, baseManufacturer, category, baseVehicles, isUniversalBase,
                CASE 
                WHEN recommendPart IS NOT NULL AND 
                        (isUniversalBase OR isUniversalRec OR 
                        ANY(v IN baseVehicles WHERE v IN recVehicles)) 
                THEN {
                    part: recommendPart,
                    manufacturer: recManufacturer,
                    vehicles: recVehicles,
                    isUniversal: isUniversalRec
                }
                ELSE NULL
                END AS validRecommendation

            // 유효한 추천 부품만 수집하고 제한
            WITH basePart, baseManufacturer, category, baseVehicles, isUniversalBase,
                [rec IN COLLECT(validRecommendation) WHERE rec IS NOT NULL][0..2] AS limitedRecommendations

            RETURN 
            basePart.model_no AS base_model_no,
            basePart.name_ko AS base_name_ko,
            COALESCE(baseManufacturer.name_en, 'Unknown') AS base_manufacturer_name,
            COALESCE(baseManufacturer.ranking, 0) AS base_manufacturer_ranking,
            COALESCE(category.name, 'Unknown') AS category_name,
            basePart.price AS base_price,
            isUniversalBase AS is_universal,
            CASE 
                WHEN isUniversalBase THEN ['all']
                WHEN SIZE(baseVehicles) = 0 THEN ['N/A']
                ELSE [v IN baseVehicles | v.model + ' (' + COALESCE(v.trim, 'Base') + ', ' + toString(v.year_start) + '-' + toString(COALESCE(v.year_end, 'Present')) + ')']
            END AS base_vehicles,
            SIZE(limitedRecommendations) AS recommendation_count,
            [rec IN limitedRecommendations | {
                model_no: rec.part.model_no,
                name_ko: rec.part.name_ko,
                name_en: rec.part.name_en,
                price: rec.part.price,
                manufacturer_name: rec.manufacturer.name_en,
                manufacturer_ranking: rec.manufacturer.ranking,
                compatible_vehicles: CASE 
                WHEN rec.isUniversal THEN ['all']
                WHEN SIZE(rec.vehicles) = 0 THEN ['N/A']
                ELSE [v IN rec.vehicles | v.model + ' (' + COALESCE(v.trim, 'Base') + ', ' + toString(v.year_start) + '-' + toString(COALESCE(v.year_end, 'Present')) + ')']
                END
            }] AS recommended_parts
                    """)
    
    all_results = {}
    
    # 각 기준 부품에 대해 개별적으로 쿼리 실행
    for model_no in input_model_nos:
        try:
            results = graph.query(query, {"input_model_no": model_no})
            row = results[0]  # 기준 부품당 하나의 결과 행
            all_results[model_no] = {
            "base_info": {
                "model_no": row["base_model_no"],
                "name_ko": row["base_name_ko"],
                "manufacturer_name": row["base_manufacturer_name"],
                "manufacturer_ranking": row.get("base_manufacturer_ranking"), # 없을 경우 None
                #"manufacturer_strength": row.get("rec_manufacturer_strength"), 
                #"manufacturer_weakness": row.get("rec_manufacturer_weakness"), 
                "category_name": row["category_name"],
                "base_price": row["base_price"],
                "base_vehicles": row["base_vehicles"]
            },
            "recommendation_count": row["recommendation_count"],
            "recommendations": row["recommended_parts"]
            }
            logger.info(f"추천 부품 {model_no}: {row['recommendation_count']}개")

        except Exception as e:
          logger.warning(f"Error processing {model_no}: {str(e)}")
          all_results[model_no] = {
              "base_info": {
                "model_no": model_no,
                "name_ko": None,
                "manufacturer_name": None,
                "manufacturer_ranking": None,
                "manufacturer_strength": None,
                "manufacturer_weakness": None,
                "category_name": None,
                "base_price": None,
                "base_vehicles": []
            },
              "recommendation_count": 0,
              "recommendations": []
          }
    elapsed_time = time.time() - start_time
    logger.info(f"부품 추천 완료 - 총 시간: {elapsed_time:.2f}초, 추천 결과 수: {len(all_results)}개")
    return all_results


def print_recommendations(recommendations: Dict[str, Dict[str, Any]]):
    for base_model_no, result in recommendations.items():
        base_info = result["base_info"]
        recommendations_list = result["recommendations"]
        logger.info(f"=== [{base_model_no} 연관 추천 상품] ===")
        logger.info(f"기준 부품명: {base_info['name_ko']}")
        logger.info(f"카테고리: {base_info['category_name']}")
        logger.info(f"가격: ${base_info['base_price']}")
        logger.info(f"제조사: {base_info['manufacturer_name']}")
        logger.info(f"제조사 랭킹: {base_info.get('manufacturer_ranking')}")
        # 기준 부품의 적용 차종 정보 출력
        base_vehicles = base_info.get('base_vehicles', [])
        if base_vehicles:
            vehicles_str = ', '.join(base_vehicles)
            logger.info(f"적용 차종: {vehicles_str}")
        logger.info(f"추천 개수: {result['recommendation_count']}")
        if recommendations_list:
            logger.info("추천 부품:")
            for i, rec in enumerate(recommendations_list, 1):
                logger.info(f"{i}. {rec['model_no']}: {rec['name_ko']}")
                logger.info(f"- 영문명: {rec['name_en']}")
                logger.info(f"- 가격: ${rec['price']}")
                logger.info(f"- 제조사: {rec['manufacturer_name']}")
                logger.info(f"- 제조사 랭킹: {rec.get('manufacturer_ranking')}")
                if rec.get('compatible_vehicles'):
                    vehicles_str = ', '.join(rec['compatible_vehicles'])
                    logger.info(f"- 적용 차종: {vehicles_str}")
        else:
            logger.info("추천 부품: 없음")

def neo4j_graph():
    graph = Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
    )
    return graph