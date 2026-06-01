"""지사 간 업무 소통에서 자주 쓰는 용어집.

단순 번역이 비즈니스 문맥을 놓치는 문제를 막기 위해, 프롬프트에 주입할
'고정 번역 규칙'을 정의한다. 키는 한국어 업무 용어, 값은 언어별 권장 표현이다.
"""

GLOSSARY = {
    "vi": {
        "발주": "đặt hàng (PO)",
        "납기": "thời hạn giao hàng",
        "견적": "báo giá",
        "불량": "lỗi/hàng lỗi",
        "재고": "tồn kho",
        "출하": "xuất hàng",
        "공정": "công đoạn sản xuất",
        "검수": "nghiệm thu",
    },
    "es": {
        "발주": "orden de compra (PO)",
        "납기": "fecha de entrega",
        "견적": "cotización",
        "불량": "producto defectuoso",
        "재고": "inventario",
        "출하": "despacho/envío",
        "공정": "proceso de producción",
        "검수": "inspección de recepción",
    },
    "en": {
        "발주": "purchase order (PO)",
        "납기": "delivery deadline",
        "견적": "quotation",
        "불량": "defective product",
        "재고": "inventory/stock",
        "출하": "shipment",
        "공정": "production process",
        "검수": "incoming inspection",
    },
}

LANGUAGE_NAMES = {
    "vi": "베트남어 (Tiếng Việt)",
    "es": "스페인어 (Español)",
    "en": "영어 (English)",
}


def relevant_terms(text: str, lang: str) -> dict:
    """입력 텍스트에 실제로 등장하는 용어만 추려서 반환한다."""
    terms = GLOSSARY.get(lang, {})
    return {ko: tr for ko, tr in terms.items() if ko in text}
