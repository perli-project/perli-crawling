import pymysql
import json
from typing import List, Dict, Any


class CardDatabase:
    """MySQL 데이터베이스 연결 및 카드 데이터 저장을 관리하는 클래스입니다.

    Attributes:
        db_config (dict): DB 접속 정보(host, user, password, db, charset).
        conn (pymysql.connections.Connection): DB 연결 객체.
        cursor (pymysql.cursors.Cursor): SQL 실행을 위한 커서 객체.
    """

    def __init__(self, db_config: Dict[str, Any]):
        """CardDatabase 인스턴스를 초기화합니다.

        Args:
            db_config (Dict[str, Any]): DB 연결 설정 정보가 담긴 딕셔너리.
        """
        self.db_config = db_config
        self.conn = None
        self.cursor = None

    def connect(self):
        """데이터베이스에 연결을 시도합니다.

        Raises:
            Exception: DB 연결 실패 시 예외를 발생시킵니다.
        """
        try:
            self.conn = pymysql.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            print("[INFO] DB 연결 성공")
        except Exception as e:
            print(f"[ERROR] DB 연결 실패: {e}")
            raise e

    def close(self):
        """데이터베이스 연결을 안전하게 종료합니다."""
        if self.conn:
            self.conn.close()
            print("[INFO] DB 연결 종료")

    def save_cards(self, card_list: List[Dict[str, Any]]):
        """파싱된 카드 데이터 리스트를 DB에 저장합니다.

        모든 데이터는 'card_info' 테이블에 저장되며, 혜택 정보(sections)는
        JSON 포맷으로 직렬화되어 'sections' 컬럼에 저장됩니다.

        Args:
            card_list (List[Dict[str, Any]]): 파싱된 카드 딕셔너리 리스트.
                구조: [{'card_name': str, 'image_url': str, 'detail_link': str, 'sections': dict}, ...]

        Raises:
            Exception: 데이터 저장 중 오류 발생 시 트랜잭션을 롤백하고 예외를 발생시킵니다.
        """
        if not self.conn:
            self.connect()

        try:
            print(f"[INFO] {len(card_list)}개의 카드 데이터 저장을 시작합니다...")

            # [1] SQL 쿼리 정의 (컬럼 순서 확인: 이름 -> 이미지 -> 링크 -> JSON)
            sql = """
                  INSERT INTO card_info (card_name, image_url, detail_link, sections)
                  VALUES (%s, %s, %s, %s) \
                  """

            for card in card_list:
                # 딕셔너리(sections) -> JSON 문자열 변환 (한글 깨짐 방지)
                sections_json = json.dumps(card['sections'], ensure_ascii=False)

                # [2] 데이터 매핑 (SQL 컬럼 순서와 정확히 일치시켜야 함)
                self.cursor.execute(sql, (
                    card['card_name'],  # 1. card_name
                    card['image_url'],  # 2. image_url
                    card['detail_link'],  # 3. detail_link
                    sections_json  # 4. sections (JSON 문자열)
                ))

            self.conn.commit()
            print("[INFO] DB 저장 완료. 모든 데이터가 커밋되었습니다.")

        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] 저장 중 에러 발생: {e}")
            raise e