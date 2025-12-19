import time
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException


class CardGorillaCrawler:
    """
    카드고릴라 웹사이트에서 카드 정보를 수집(크롤링)하는 클래스이다.

    Attributes:
        output_file (str): 수집된 데이터를 저장할 파일 경로.
        base_url (str): 크롤링을 시작할 카드고릴라 메인 URL.
        driver (webdriver.Chrome): Selenium Chrome 드라이버 인스턴스.
    """

    def __init__(self, output_file: str = "all_cards_result.txt"):
        """
        크롤러 인스턴스를 초기화하고 기본 설정을 수행한다.

        Args:
            output_file (str): 결과 저장 파일명 (기본값: "all_cards_result.txt").
        """
        self.output_file = output_file
        self.base_url = "https://www.card-gorilla.com/team/detail/2"
        self.driver = self._setup_driver()

    def _setup_driver(self) -> webdriver.Chrome:
        """
        Chrome WebDriver를 설정하고 실행한다.

        화면 크기, 샌드박스 비활성화, User-Agent 등의 옵션을 설정하여
        봇 탐지를 방지하고 안정적인 크롤링 환경을 구성한다.

        Returns:
            webdriver.Chrome: 설정이 완료된 Chrome 드라이버 객체.
        """
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def _expand_list(self):
        """
        현재 페이지의 리스트를 끝까지 확장한다.

        화면에 '더보기' 버튼이 존재하는 동안 반복해서 클릭하여
        모든 카드가 리스트에 노출되도록 한다.
        """
        print("   >>> 리스트 전체 로딩 중 (더보기 클릭)...")
        while True:
            try:
                more_btn = self.driver.find_element(By.CSS_SELECTOR, "a.lst_more")
                if more_btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", more_btn)
                    time.sleep(1.5)
                else:
                    break
            except (NoSuchElementException, StaleElementReferenceException):
                break
            except Exception:
                break

    def _get_card_links(self) -> List[str]:
        """
        현재 펼쳐진 리스트에서 각 카드의 상세 페이지 URL을 추출하여 반환한다.

        Returns:
            List[str]: 수집된 카드 상세 페이지 URL 리스트.
        """
        card_urls = []
        try:
            list_container = self.driver.find_element(By.CLASS_NAME, "results_lst")
            links = list_container.find_elements(By.TAG_NAME, "a")
            for link in links:
                try:
                    href = link.get_attribute("href")
                    # 유효한 상세 페이지 링크인지 검증
                    if href and "/card/detail" in href and href not in card_urls:
                        card_urls.append(href)
                except StaleElementReferenceException:
                    continue
        except Exception:
            print("   >>> 카드 리스트 영역을 찾지 못했다.")
        return card_urls

    def _parse_card_detail(self, url: str, file_handle):
        """
        특정 카드 상세 페이지에 접속하여 정보를 파싱하고 파일에 기록한다.

        단종된 카드는 식별하여 건너뛰며, 정상 카드일 경우
        카드명, 이미지 URL, 상세 링크, 혜택 정보를 수집한다.

        Args:
            url (str): 접속할 카드 상세 페이지 URL.
            file_handle (TextIOWrapper): 데이터를 기록할 열린 파일 객체.
        """
        self.driver.get(url)
        time.sleep(2)

        # 1. 단종 체크 (신규 발급 중단 여부 확인)
        try:
            stop_msg = self.driver.find_elements(By.XPATH, "//*[contains(text(), '신규발급이 중단된 카드입니다')]")
            if stop_msg:
                print(" -> [SKIP] 단종된 카드")
                file_handle.write(f"\n■ (단종) 링크: {url}\n")
                file_handle.write("  - 신규 발급 중단으로 스킵함\n")
                file_handle.write("-" * 30 + "\n")
                return  # 함수 종료
        except Exception:
            pass

        # 2. 카드 이름 수집
        try:
            card_name = self.driver.find_element(By.CSS_SELECTOR, "strong.card").text
        except:
            card_name = "이름 불명"

        # 3. 이미지 링크 수집
        try:
            img_src = self.driver.find_element(By.CSS_SELECTOR, "div.card_img img").get_attribute("src")
        except:
            img_src = "이미지 없음"

        print(f" -> {card_name}")
        file_handle.write(f"\n■ {card_name}\n")
        file_handle.write(f"이미지: {img_src}\n")
        file_handle.write(f"상세링크: {url}\n")

        # 4. 혜택 정보 수집 및 기록
        self._extract_benefits(file_handle)
        file_handle.write("-" * 30 + "\n")

    def _extract_benefits(self, file_handle):
        """
        상세 페이지 내의 혜택 정보(아코디언 메뉴)를 펼쳐서 텍스트를 추출한다.

        Args:
            file_handle (TextIOWrapper): 데이터를 기록할 열린 파일 객체.
        """
        try:
            # 주요 혜택 영역 찾기 (h3 태그 기준)
            bene_area = self.driver.find_element(By.XPATH,
                                                 "//h3[contains(text(), '주요혜택')]/following-sibling::div[contains(@class, 'bene_area')]")
            dl_list = bene_area.find_elements(By.TAG_NAME, "dl")

            has_benefit = False
            for dl in dl_list:
                try:
                    # 혜택 제목 추출
                    dt = dl.find_element(By.TAG_NAME, "dt")
                    try:
                        title = dt.find_element(By.TAG_NAME, "i").text
                    except:
                        title = dt.text.split('\n')[0]

                    # 아코디언 메뉴 클릭 (펼치기)
                    self.driver.execute_script("arguments[0].click();", dt)
                    time.sleep(0.2)

                    # 혜택 상세 내용 추출 및 포맷팅
                    in_box = dl.find_element(By.CSS_SELECTOR, "dd div.in_box")
                    content = in_box.text.strip().replace("\n", "\n    ")

                    file_handle.write(f"[{title}]\n    {content}\n")
                    has_benefit = True
                except:
                    continue

            if not has_benefit:
                file_handle.write("  (혜택 정보 텍스트 없음)\n")

        except Exception:
            file_handle.write("  (주요 혜택 영역 없음)\n")

    def run(self):
        """
        크롤링 전체 프로세스를 실행한다.

        1. 메인 페이지 접속 및 카드사 목록 파악
        2. 각 카드사별 페이지 이동
        3. '더보기'를 통한 전체 리스트 로딩
        4. 상세 페이지 순회 및 데이터 수집
        5. 결과 파일 저장
        """
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                print(f">>> 초기 페이지 접속: {self.base_url}")
                self.driver.get(self.base_url)
                time.sleep(3)

                # 카드사 개수 파악
                try:
                    companies = self.driver.find_elements(By.CSS_SELECTOR, "li.company-name")
                    total_companies = len(companies)
                    print(f">>> 발견된 카드사 개수: {total_companies}개")
                except:
                    print("카드사 목록을 찾을 수 없다.")
                    return

                # 카드사 순회
                for comp_idx in range(total_companies):
                    try:
                        # 요소 재탐색 (Stale 방지)
                        current_companies = self.driver.find_elements(By.CSS_SELECTOR, "li.company-name")
                        if comp_idx >= len(current_companies): break

                        target_company = current_companies[comp_idx]
                        company_name = target_company.text

                        print(f"\n[{comp_idx + 1}/{total_companies}] 카드사 이동: {company_name}")
                        f.write(f"\n\n{'=' * 50}\n[[ 카드사: {company_name} ]]\n{'=' * 50}\n")

                        # 카드사 클릭
                        self.driver.execute_script("arguments[0].click();", target_company)
                        time.sleep(4)

                        # 리스트 확장 및 링크 수집
                        self._expand_list()
                        card_urls = self._get_card_links()
                        print(f"   >>> 수집된 카드 개수: {len(card_urls)}개")

                        # 상세 페이지 순회
                        for i, url in enumerate(card_urls):
                            print(f"   [{i + 1}/{len(card_urls)}] 확인 중... ", end="")
                            self._parse_card_detail(url, f)

                        # 목록 복귀
                        self.driver.get(self.base_url)
                        time.sleep(3)

                    except Exception as e:
                        print(f"   !!! 카드사 처리 중 에러: {e}")
                        self.driver.get(self.base_url)
                        time.sleep(3)
                        continue

            print(f"\n>>> 모든 작업 완료! '{self.output_file}' 파일을 확인하라.")

        except Exception as e:
            print(f"시스템 치명적 에러: {e}")
        finally:
            self.driver.quit()