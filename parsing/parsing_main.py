from pathlib import Path
from parsing import parse_cards_text
from database.db_utils import CardDatabase


def main():
    """프로그램의 메인 진입점입니다.

    1. 텍스트 파일을 상위 디렉토리에서 찾습니다.
    2. 파일을 읽어 파싱 모듈로 데이터를 구조화합니다.
    3. DB 모듈을 통해 데이터를 저장합니다.
    """

    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '011020',  # DB 비밀번호
        'db': 'saranghaein',  # 스키마 이름
        'charset': 'utf8mb4'
    }

    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    file_path = project_root / "all_cards_result.txt"

    if not file_path.exists():
        print(f"파일을 찾을 수 없습니다.")
        print(f"탐색 경로: {file_path}")
        return

    print(f"파일을 찾았습니다: {file_path}")
    print("파일 읽기 시작...")

    try:
        # 인코딩 처리: cp949(윈도우) 시도 후 실패 시 utf-8-sig
        raw_text = file_path.read_text(encoding="cp949")
    except UnicodeDecodeError:
        raw_text = file_path.read_text(encoding="utf-8-sig")

    card_data_list = parse_cards_text(raw_text)
    print(f"[INFO] 파싱 완료. {len(card_data_list)}개의 데이터가 준비되었습니다.")

    if not card_data_list:
        print("[WARN] 저장할 데이터가 없습니다. 프로그램을 종료합니다.")
        return

    db = CardDatabase(db_config)
    try:
        db.save_cards(card_data_list)
    except Exception as e:
        print(f"[ERROR] 작업 중 오류 발생: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()