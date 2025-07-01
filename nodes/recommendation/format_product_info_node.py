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

    for base_model_no, hit in neo4j_hits.items():
        base = hit.get("base_info", {})

        if not isinstance(base, dict):
            logger.warning(f"[format_product_recommendations] base_info 누락 또는 비정상 for {base_model_no}")
            continue
        
        recommendations = hit.get("recommendations", [])

        # 기준 부품 정보 추출 (누락 시 '정보 없음')
        name_ko = base.get("product_name_ko", "정보 없음")
        price = base.get("price", "정보 없음")
        price_str = f"${price:.2f}" if isinstance(price, (int, float)) else "정보 없음"
        manufacturer = base.get("manufacturer_name", "정보 없음")
        manufacturer_rank = base.get("manufacturer_ranking")
        manufacturer_rank_str = str(manufacturer_rank) if manufacturer_rank is not None else "정보 없음"
        category = base.get("category_name", "정보 없음")
        product_url = base.get("product_url", "정보 없음")
        rec_count = hit.get("recommendation_count", 0)

        lines.append(f"[기준 부품] {base_model_no}")
        lines.append(f"- 제품명: {name_ko}")
        lines.append(f"- 가격: {price_str}")
        lines.append(f"- 제조사: {manufacturer} (랭킹: {manufacturer_rank_str})")
        lines.append(f"- 카테고리: {category}")
        lines.append(f"- 상품 URL: {product_url}")
        lines.append(f"- 추천 부품 수: {rec_count}")
        
        if not recommendations:
            logger.warning(f"[format_product_recommendations] '{base_model_no}'은 추천이 없어 생략됨.")
    
        else:
            for idx, rec in enumerate(recommendations, 1):
                rec_model_no = rec.get("model_no", "정보 없음")
                rec_name_ko = rec.get("name_ko", "정보 없음")
                rec_price = rec.get("price")
                rec_price_str = f"${rec_price:.2f}" if isinstance(rec_price, (int, float)) else "정보 없음"
                rec_manufacturer = rec.get("manufacturer_name", "정보 없음")
                rec_rank = rec.get("manufacturer_ranking")
                rec_rank_str = str(rec_rank) if rec_rank is not None else "정보 없음"
                compatible_vehicles = rec.get("compatible_vehicles") or []
                vehicles_str = ", ".join(compatible_vehicles) if compatible_vehicles else "정보 없음"
                rec_product_url = rec.get("product_url", "정보 없음")

                lines.append(f"\n  [추천 부품 {idx}]")
                lines.append(f"  - 모델번호: {rec_model_no}")
                lines.append(f"  - 제품명: {rec_name_ko}")
                lines.append(f"  - 가격: {rec_price_str}")
                lines.append(f"  - 제조사: {rec_manufacturer} (랭킹: {rec_rank_str})")
                lines.append(f"  - 호환 차종: {vehicles_str}")
                lines.append(f"  - 상품 URL: {rec_product_url}")

        lines.append("")

    return "\n".join(lines)
