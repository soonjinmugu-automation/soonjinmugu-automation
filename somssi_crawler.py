from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os
import pickle

class SomssiCrawler:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None
        self.cookie_file = os.path.expanduser("~/자동화/cookies/somssi_cookies.pkl")

    def setup_driver(self, use_profile=True):
        """Chrome 드라이버 설정"""
        import subprocess

        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')

        # 순진무구 크롬 프로필 사용 (soonjinmugu.studio@gmail.com)
        if use_profile:
            # 크롬이 실행 중인지 확인
            result = subprocess.run(['pgrep', '-x', 'Google Chrome'], capture_output=True)
            if result.returncode == 0:
                print("⚠️ 크롬이 실행 중 - 일반 모드로 실행합니다.")
                print("   (자동 로그인을 원하시면 크롬을 종료 후 다시 실행해주세요)")
            else:
                print("✅ 크롬 프로필 사용 (순진무구)")
                chrome_user_data = os.path.expanduser("~/Library/Application Support/Google/Chrome")
                options.add_argument(f"--user-data-dir={chrome_user_data}")
                options.add_argument("--profile-directory=Profile 4")

        self.driver = webdriver.Chrome(service=service, options=options)
        return self.driver

    def save_cookies(self):
        """쿠키 저장 (조용히)"""
        try:
            os.makedirs(os.path.dirname(self.cookie_file), exist_ok=True)
            with open(self.cookie_file, 'wb') as f:
                pickle.dump(self.driver.get_cookies(), f)
        except:
            pass

    def load_cookies(self):
        """쿠키 로드 (조용히)"""
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, 'rb') as f:
                    cookies = pickle.load(f)
                    for cookie in cookies:
                        try:
                            self.driver.add_cookie(cookie)
                        except:
                            pass
                return True
            except:
                pass
        return False

    def handle_alert(self):
        """Alert 창 처리"""
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
            time.sleep(0.5)
            return True
        except:
            return False

    def login(self):
        """솜씨당 네이버 소셜 로그인 (크롬 프로필 사용)"""
        print("🔐 솜씨당 로그인 중...")

        # 먼저 솜씨당 메인으로 이동 (쿠키 로드를 위해)
        self.driver.get("https://www.sssd.co.kr")
        time.sleep(1)

        # 저장된 쿠키 로드 시도
        if self.load_cookies():
            self.driver.refresh()
            time.sleep(2)

        # 캘린더 페이지로 이동
        self.driver.get("https://www.sssd.co.kr/host/calendar/authorCalendar.do")
        time.sleep(3)
        self.handle_alert()

        # 이미 로그인되어 있는지 확인
        if "authorLogin" not in self.driver.current_url:
            print("✅ 솜씨당 자동 로그인 성공!")
            self.save_cookies()  # 쿠키 저장
            return True

        # Alert 반복 처리
        for _ in range(5):
            if not self.handle_alert():
                break
            time.sleep(0.5)

        try:
            # 네이버 로그인 버튼 자동 클릭
            naver_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.login-btn-naver"))
            )
            self.handle_alert()
            naver_btn.click()
            time.sleep(2)

            # 네이버에 이미 로그인되어 있으면 자동으로 리다이렉트됨
            manual_login_notified = False
            naver_wait_count = 0
            for i in range(60):
                time.sleep(1)
                current_url = self.driver.current_url or ""

                # 솜씨당 호스트 페이지로 리다이렉트되면 성공
                if current_url and "sssd.co.kr/host" in current_url and "authorLogin" not in current_url:
                    print("✅ 솜씨당 자동 로그인 성공!")
                    time.sleep(1)
                    self.handle_alert()
                    self.save_cookies()  # 쿠키 저장
                    return True

                # 네이버 로그인 페이지 체크
                if current_url and "naver.com" in current_url:
                    naver_wait_count += 1
                    # 5초 이상 네이버 페이지에 머물면 수동 로그인 필요
                    if naver_wait_count >= 5 and not manual_login_notified:
                        print("=" * 50)
                        print("👆 네이버 로그인이 필요합니다.")
                        print("   브라우저에서 로그인을 완료해주세요!")
                        print("=" * 50)
                        manual_login_notified = True

            # 최종 확인
            self.driver.get("https://www.sssd.co.kr/host/calendar/authorCalendar.do")
            time.sleep(3)
            self.handle_alert()

            if "authorLogin" in self.driver.current_url:
                print("❌ 로그인 실패 - 다시 시도해주세요")
                return False

            print("✅ 솜씨당 로그인 완료!")
            self.save_cookies()
            return True

        except Exception as e:
            print(f"❌ 로그인 실패: {e}")
            return False

    def get_reservations(self):
        """예약 목록 가져오기"""
        print("📋 솜씨당 예약 목록 조회 중...")
        reservations = []

        try:
            # 캘린더 페이지로 이동
            self.driver.get("https://www.sssd.co.kr/host/calendar/authorCalendar.do")
            time.sleep(3)
            self.handle_alert()

            print("📅 캘린더 로드 완료!")

            # 월별 뷰로 변경 시도 (더 많은 날짜 표시)
            try:
                month_btn = self.driver.find_element(By.CSS_SELECTOR, "button.fc-month-button, .fc-month-button")
                month_btn.click()
                time.sleep(1)
                print("📅 월별 뷰로 전환")
            except:
                pass  # 이미 월별 뷰이거나 버튼 없음

            # 모든 수업 이벤트 찾기 (모든 타입)
            events = self.driver.find_elements(By.CSS_SELECTOR, "a.fc-event")
            print(f"📌 총 {len(events)}개 수업 발견")

            for i, event in enumerate(events):
                try:
                    # fc-time이 없는 이벤트는 스킵 (종일 이벤트, 통계 등)
                    time_elems = event.find_elements(By.CSS_SELECTOR, "span.fc-time")
                    if not time_elems:
                        continue

                    time_elem = time_elems[0]
                    title_elem = event.find_element(By.CSS_SELECTOR, "span.fc-title")
                    class_title_elem = event.find_element(By.CSS_SELECTOR, "span.fc-class-title")

                    class_time = time_elem.text.strip()  # "13:00"
                    people_text = title_elem.text.strip()  # "2/7명"
                    class_title = class_title_elem.text.strip()  # "[송파/잠실] 이모티콘..."

                    # 현재 인원 추출
                    people_match = re.search(r'(\d+)/\d+명', people_text)
                    current_people = int(people_match.group(1)) if people_match else 0

                    if current_people == 0:
                        continue  # 예약자가 없으면 스킵

                    # 장소 추출 (클래스 제목에서)
                    location_match = re.search(r'\[([^\]]+)\]', class_title)
                    location = location_match.group(1) if location_match else ""

                    # 이벤트 클릭하여 상세 정보 확인
                    event.click()
                    time.sleep(1.5)
                    self.handle_alert()

                    # 모달에서 참여자 정보 추출
                    try:
                        modal = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".modal.show"))
                        )
                        time.sleep(2)  # 모달 내용 로딩 대기 시간 증가

                        # 일정 날짜 추출
                        schedule_date = ""
                        try:
                            date_input = modal.find_element(By.CSS_SELECTOR, "#scheduleStartDate")
                            schedule_date = date_input.get_attribute("value")
                        except:
                            pass

                        # 안심번호발급 버튼 클릭 (미할당인 경우)
                        try:
                            reissue_btns = modal.find_elements(By.CSS_SELECTOR, "span.bizCallReqBtn")
                            for btn in reissue_btns:
                                try:
                                    btn.click()
                                    print("🔄 안심번호발급 클릭")
                                    time.sleep(1)

                                    # 확인 버튼 클릭 (alert 또는 confirm 창)
                                    try:
                                        alert = self.driver.switch_to.alert
                                        alert.accept()
                                        print("✅ 확인 클릭")
                                        time.sleep(2)
                                    except:
                                        # alert가 아닌 경우 모달 내 확인 버튼 찾기
                                        try:
                                            confirm_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '확인')]")
                                            confirm_btn.click()
                                            print("✅ 확인 버튼 클릭")
                                            time.sleep(2)
                                        except:
                                            pass
                                except:
                                    pass
                        except:
                            pass

                        # 모달 HTML 다시 가져오기 (발급 후 업데이트된 내용)
                        time.sleep(0.5)

                        # 참여자 정보 추출 (이름 + 안심번호 + 인원수)
                        participants = []
                        try:
                            modal_html = modal.get_attribute('innerHTML')

                            # 이름 추출 (mebName)
                            names = re.findall(r'id="mebName"[^>]*value="([^"]*)"', modal_html)
                            # 전화번호 추출 (mebHp)
                            phones = re.findall(r'id="mebHp"[^>]*>([^<]*)<', modal_html)
                            # 인원수 추출 (mebCnt 또는 inwr)
                            people_counts = re.findall(r'id="(?:mebCnt|inwr)"[^>]*value="([^"]*)"', modal_html)

                            # 이름과 전화번호 매칭
                            for idx, name in enumerate(names):
                                name = name.strip()
                                if not name:
                                    continue

                                # 전화번호가 있으면 사용, 없으면 빈 문자열
                                phone = phones[idx].strip() if idx < len(phones) else ""
                                # 인원수가 있으면 사용, 없으면 '1'
                                people_count = people_counts[idx].strip() if idx < len(people_counts) and people_counts[idx].strip() else '1'

                                # 전화번호가 050으로 시작하면 안심번호
                                # 전화번호가 없거나 빈 문자열이면 "미할당"으로 표시
                                if phone.startswith('050'):
                                    participants.append({'name': name, 'phone': phone, 'people': people_count})
                                elif phone == "" or not phone:
                                    participants.append({'name': name, 'phone': '미할당', 'people': people_count})
                                else:
                                    participants.append({'name': name, 'phone': phone, 'people': people_count})

                        except:
                            pass

                        # 모달 닫기 (X 버튼 클릭)
                        try:
                            close_btn = modal.find_element(By.CSS_SELECTOR, "button.close")
                            close_btn.click()
                            time.sleep(0.5)
                        except:
                            pass

                        # 모달이 닫힐 때까지 대기
                        try:
                            WebDriverWait(self.driver, 3).until(
                                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".modal.show"))
                            )
                        except:
                            from selenium.webdriver.common.keys import Keys
                            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                            time.sleep(0.5)

                        # 예약 정보 저장
                        for p in participants:
                            datetime_str = f"{schedule_date} {class_time}" if schedule_date else class_time
                            people_count = p.get('people', '1')  # 인원수 (기본값 1)
                            reservation = {
                                'platform': '솜씨당',
                                'name': p['name'],
                                'phone': p['phone'],
                                'people': people_count,
                                'datetime': datetime_str,
                                'location': location,
                                'class_title': class_title,
                                'status': '예약 확정'
                            }
                            reservations.append(reservation)
                            people_display = f"({people_count}명)" if people_count != '1' else ""
                            print(f"✅ 솜씨당 예약: {p['name']}{people_display} | {p['phone']} | {datetime_str} | {location}")

                    except Exception as modal_e:
                        print(f"⚠️ 모달 처리 실패: {modal_e}")
                        # 모달이 열려있으면 닫기 시도
                        try:
                            from selenium.webdriver.common.keys import Keys
                            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                            time.sleep(0.5)
                        except:
                            pass

                except Exception as e:
                    print(f"⚠️ 이벤트 {i+1} 처리 실패: {e}")
                    continue

            print(f"\n✅ 총 {len(reservations)}개 예약 발견")
            return reservations

        except Exception as e:
            print(f"❌ 예약 조회 실패: {e}")
            import traceback
            traceback.print_exc()
            return []

    def close(self):
        if self.driver:
            self.driver.quit()


# 테스트 코드
if __name__ == "__main__":
    crawler = SomssiCrawler("", "")

    try:
        crawler.setup_driver()
        if crawler.login():
            crawler.get_reservations()
    finally:
        crawler.close()
