from typing import Dict, Any
from jeepchat.logger import logger

def format_product_info_node(state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        neo4j_hits = state.get("neo4j_hits", {})
        product_info = format_product_recommendations(neo4j_hits=neo4j_hits)
        logger.debug(f"[format_product_info_node] 추천 제품 포맷:\n{product_info}")
        
        return {
            **state,
            "product_info": product_info
        }

    except Exception as e:
        logger.error(f"[format_product_info_node] 포맷팅 중 오류 발생: {e}", exc_info=True)
        return {
            **state,
            "product_info": "",
            "output": "추천 정보  포맷팅 중 오류가 발생했습니다."
        }

def format_product_recommendations(neo4j_hits: Dict[str, Dict[str, Any]]) -> str:
    lines = []

    for base_hit in neo4j_hits.values():
        base = base_hit["base_info"]
        lines.append(f"모델번호: {base.get('model_no', '')}")
        lines.append(f"제품명: {base.get('name_ko', '')}")
        lines.append(f"가격: ${base.get('base_price', 0):.2f}")
        lines.append(f"제조사: {base.get('manufacturer_name', '')}")
        lines.append(f"카테고리: {base.get('category_name', '')}")
        lines.append(f"추천 부품 수: {base_hit.get('recommendation_count', 0)}")

        lines.extend([
            f"- 추천 모델번호: {rec.get('model_no', '')}\n"
            f"  제품명: {rec.get('name_ko', '')}\n"
            f"  가격: ${rec.get('price', 0):.2f}"
            for rec in base_hit.get("recommendations", [])
        ])

        lines.append("")

    return "\n".join(lines)