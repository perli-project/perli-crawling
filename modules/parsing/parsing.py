import unicodedata
from typing import List, Dict, Optional, Any


def clean_text(text: str) -> str:
    """문자열을 정규화하고 불필요한 특수 공백을 제거합니다.

    Args:
        text (str): 정제할 원본 문자열.

    Returns:
        str: NFC 정규화가 적용되고 특수 공백이 제거된 문자열.
    """
    if not text: return ""
    text = unicodedata.normalize('NFC', text)
    text = text.replace('\u00a0', ' ')
    return text


def parse_cards_text(text: str) -> List[Dict[str, Any]]:
    """텍스트 파일 내용을 파싱하여 구조화된 카드 데이터 리스트로 변환합니다.

    텍스트를 줄 단위로 읽어 구분선, 가짜 헤더 등을 처리하고
    카드 이름, 이미지, 상세 링크, 혜택 정보를 추출합니다.

    Args:
        text (str): 파일에서 읽어온 전체 텍스트 내용.

    Returns:
        List[Dict[str, Any]]: 파싱된 카드 정보 딕셔너리들의 리스트.
            각 딕셔너리는 'card_name', 'image_url', 'detail_link', 'sections' 키를 포함합니다.
    """
    lines = text.splitlines()
    cards = []
    card: Optional[Dict] = None
    current_section: Optional[str] = None
    buffer: List[str] = []

    def flush_section():
        """현재 버퍼에 담긴 내용을 합쳐서 현재 카드의 섹션에 저장합니다."""
        nonlocal buffer, current_section, card
        if card is not None and current_section is not None and buffer:
            clean_lines = [line.strip() for line in buffer if line.strip()]

            if current_section in card["sections"]:
                card["sections"][current_section] += "\n" + "  ".join(clean_lines)
            else:
                card["sections"][current_section] = "  ".join(clean_lines)
        buffer = []

    def flush_card():
        """현재 처리 중인 카드 정보를 리스트에 추가하고 상태를 초기화합니다."""
        nonlocal card, current_section, buffer
        flush_section()
        if card is not None:
            cards.append(card)
        card = None
        current_section = None
        buffer = []

    divider_check = "-----"

    for line in lines:
        line = clean_text(line)
        stripped = line.strip()

        if divider_check in stripped: continue
        if stripped.startswith("=="): continue
        if stripped.startswith("[[ 카드사"): continue

        if stripped.startswith("■"):
            temp_name = stripped.replace("■", "", 1).strip()

            fake_keywords = [
                "즉시결제", "유의사항", "확인하세요", "안내사항", "참고사항",
                "서비스 적용 기준", "청구금액", "수수료", "산출방법",
                "이용시", "전신환", "적립 서비스", "할인 서비스",
                "방법", "계획소비", "적립 받는", "혜택", "실적"
            ]

            if any(keyword in temp_name for keyword in fake_keywords):
                if any(char in temp_name for char in [":", "+", "×", "~", "="]):
                    buffer.append(line)
                else:
                    if card is not None:
                        flush_section()
                        current_section = temp_name
                continue

            flush_card()

            if "(단종)" in temp_name:
                card = None
                continue

            card = {
                "card_name": temp_name,
                "image_url": None,
                "detail_link": None,
                "sections": {}
            }
            continue

        if card is None: continue

        if stripped.startswith("이미지:"):
            card["image_url"] = stripped.split(":", 1)[1].strip()
            continue

        if stripped.startswith("상세링크:"):
            card["detail_link"] = stripped.split(":", 1)[1].strip()
            continue

        if stripped.startswith("[") and stripped.endswith("]"):
            flush_section()
            clean_title = stripped.replace("[", "").replace("]", "").strip()
            current_section = clean_title
            continue

        if current_section is not None:
            buffer.append(line)

    flush_card()
    return cards