import os
import time
from dotenv import load_dotenv
from jeepchat.logger import logger
load_dotenv()
from typing import List, Dict, Any
from langchain_neo4j import Neo4jGraph

def recommend_parts(graph: Neo4jGraph, input_model_nos: List[str]) -> Dict[str, Dict[str, Any]]:
    start_time = time.time()
    logger.info(f"부품 추천 시작 - 입력 부품 수: {len(input_model_nos)}, 부품 목록: {input_model_nos}")
    
    query = """
    MATCH (basePart:Part {model_no: $input_model_no})
    MATCH (basePart)-[:MANUFACTURED_BY]->(manufacturer:Manufacturer)
    MATCH (basePart)-[:BELONGS_TO]->(category:Category)

    OPTIONAL MATCH (basePart)-[:FITS_FOR]->(v1:Vehicle)
    OPTIONAL MATCH (basePart)-[:FITS_FOR]->(:UniversalVehicle {type: 'all'})-[:COVERS]->(v2:Vehicle)
    WITH basePart, manufacturer, category,
        COLLECT(DISTINCT v1) + COLLECT(DISTINCT v2) AS baseVehicles,
        EXISTS((basePart)-[:FITS_FOR]->(:UniversalVehicle {type: 'all'})) AS isUniversalBase

    MATCH (recommendPart:Part)-[:MANUFACTURED_BY]->(manufacturer)
    MATCH (recommendPart)-[:BELONGS_TO]->(category)
    WHERE recommendPart.model_no <> basePart.model_no

    OPTIONAL MATCH (recommendPart)-[:FITS_FOR]->(cv1:Vehicle)
    OPTIONAL MATCH (recommendPart)-[:FITS_FOR]->(:UniversalVehicle {type: 'all'})-[:COVERS]->(cv2:Vehicle)
    WITH basePart, manufacturer, category, baseVehicles, isUniversalBase,
        recommendPart,
        COLLECT(DISTINCT cv1) + COLLECT(DISTINCT cv2) AS recVehicles,
        EXISTS((recommendPart)-[:FITS_FOR]->(:UniversalVehicle {type: 'all'})) AS isUniversalRec

    WHERE ANY(v IN baseVehicles WHERE v IN recVehicles)

    WITH basePart, manufacturer, category, isUniversalBase, baseVehicles,
        COLLECT(DISTINCT {
            part: recommendPart,
            isUniversal: isUniversalRec,
            vehicles: recVehicles
        })[0..2] AS limitedRecommendations

    RETURN 
      basePart.model_no AS base_model_no,
      basePart.name_ko AS base_name_ko,
      manufacturer.name_en AS manufacturer_name,
      category.name AS category_name,
      basePart.price AS base_price,
      isUniversalBase AS is_universal,
      CASE 
        WHEN isUniversalBase THEN ['all']
        ELSE [v IN baseVehicles | v.model + ' (' + COALESCE(v.trim, 'Base') + ', ' + toString(v.year_start) + '-' + toString(COALESCE(v.year_end, 'Present')) + ')']
      END AS base_vehicles,
      SIZE(limitedRecommendations) AS recommendation_count,
      [item IN limitedRecommendations | {
        model_no: item.part.model_no,
        name_ko: item.part.name_ko,
        name_en: item.part.name_en,
        price: item.part.price,
        compatible_vehicles: CASE 
          WHEN item.isUniversal THEN ['all']
          ELSE [v IN item.vehicles | v.model + ' (' + COALESCE(v.trim, 'Base') + ', ' + toString(v.year_start) + '-' + toString(COALESCE(v.year_end, 'Present')) + ')']
        END
      }] AS recommended_parts

    """
    
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
                    "manufacturer_name": row["manufacturer_name"],
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
                  "category_name": None,
                  "base_price": None,
                  "compatible_vehicles": []
              },
              "recommendation_count": 0,
              "recommendations": []
          }
    elapsed_time = time.time() - start_time
    logger.info(f"부품 추천 완료 - 총 시간: {elapsed_time:.2f}초, 추천 결과 수: {len(all_results)}개")
    return all_results

# 실행 예시
def print_recommendations(recommendations: Dict[str, Dict[str, Any]]):
    for base_model_no, result in recommendations.items():
        base_info = result["base_info"]
        recommendations_list = result["recommendations"]
        
        logger.info(f"=== [{base_model_no} 연관 추천 상품] ===")
        logger.info(f"부품명: {base_info['name_ko']}")
        logger.info(f"제조사: {base_info['manufacturer_name']}")
        logger.info(f"카테고리: {base_info['category_name']}")
        logger.info(f"가격: ${base_info['base_price']}")
        
        # 기준 부품의 적용 차종 정보 출력
        if base_info.get('base_vehicles'):
            vehicles_str = ', '.join(base_info['base_vehicles'])
            logger.info(f"적용 차종: {vehicles_str}")
        
        logger.info(f"추천 개수: {result['recommendation_count']}")
        
        if recommendations_list:
            logger.info("추천 부품:")
            for i, rec in enumerate(recommendations_list, 1):
                logger.info(f"{i}. {rec['model_no']}: {rec['name_ko']}")
                logger.info(f"- 영문명: {rec['name_en']}")
                logger.info(f"- 가격: ${rec['price']}")
                
                # 추천 부품의 적용 차종 정보 출력
                if rec.get('compatible_vehicles'):
                    vehicles_str = ', '.join(rec['compatible_vehicles'])
                    logger.info(f"- 적용 차종: {vehicles_str}")
        else:
            logger.info("추천 부품: None")

def neo4j_graph():
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
    )
    return graph


# 사용 예시
if __name__ == "__main__":
    print(os.getenv("NEO4J_URI"))
    graph = neo4j_graph()
    input_model_nos = ["SPD860605", "QKEQTE904", "TOY361150"]
    recommendations = recommend_parts(graph, input_model_nos)
    # print_recommendations(recommendations)
    print(recommendations)