from crawler import CardGorillaCrawler


def main():
    """
    프로그램의 진입점(Entry Point)이다.
    CardGorillaCrawler 인스턴스를 생성하고 크롤링 작업을 시작한다.
    """

    # 1. 크롤러 인스턴스를 생성한다.
    # 파일명을 따로 지정하고 싶다면 output_file="my_result.txt" 처럼 넣으면 된다.
    # 아무것도 안 넣으면 기본값(all_cards_result.txt)으로 설정된다.
    bot = CardGorillaCrawler()

    # 2. 크롤링 로직을 실행한다.
    bot.run()


if __name__ == "__main__":
    main()