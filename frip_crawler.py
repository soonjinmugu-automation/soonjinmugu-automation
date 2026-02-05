from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os
import subprocess

class FripCrawler:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None

    def setup_driver(self, use_profile=True):
        """Chrome 드라이버 설정"""
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')

        # 순진무구 크롬 프로필 사용
        if use_profile:
            result = subprocess.run(['pgrep', '-x', 'Google Chrome'], capture_output=True)
            if result.returncode == 0:
                print("⚠️ 크롬이 실행 중 - 일반 모드로 실행합니다.")
            else:
                print("✅ 크롬 프로필 사용 (순진무구)")
                chrome_user_data = os.path.expanduser("~/Library/Application Support/Google/Chrome")
                options.add_argument(f"--user-data-dir={chrome_user_data}")
                options.add_argument("--profile-directory=Profile 4")

        self.driver = webdriver.Chrome(service=service, options=options)
        return self.driver
    
    def login(self):
        """프립 로그인"""
        print("🔐 프립 로그인 중...")

        # 먼저 예약 관리 페이지로 이동해서 로그인 상태 확인
        self.driver.get("https://frip.host/booking/list")
        time.sleep(3)

        # 이미 로그인되어 있으면 성공
        if "sign-in" not in self.driver.current_url and "login" not in self.driver.current_url:
            print("✅ 크롬 프로필로 자동 로그인 성공!")
            return True

        print("📝 로그인 필요 - 수동 로그인 시도...")

        # 로그인 페이지로 이동
        self.driver.get("https://frip.host/sign-in")
        time.sleep(2)

        try:
            # 이메일 입력 (name="아이디(이메일)")
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='아이디(이메일)']"))
            )
            email_input.clear()
            email_input.send_keys(self.email)
            time.sleep(1)

            # 비밀번호 입력
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='비밀번호']")
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(1)

            # 로그인 버튼 클릭
            login_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '로그인')]")
            login_btn.click()

            time.sleep(5)

            # 로그인 성공 확인
            if "sign-in" not in self.driver.current_url and "login" not in self.driver.current_url:
                print("✅ 프립 로그인 완료!")
                return True
            else:
                print("❌ 로그인 실패 - 페이지 확인 필요")
                return False

        except Exception as e:
            print(f"❌ 프립 로그인 실패: {e}")
            return False
    
    def get_reservations(self):
        """예약 목록 가져오기 (새 UI 구조)"""
        print("📋 프립 예약 목록 조회 중...")
        reservations = []

        try:
            # 예약 관리 페이지로 이동
            self.driver.get("https://frip.host/booking")
            time.sleep(3)

            # 목록으로 보기 클릭
            try:
                list_view_btn = self.driver.find_element(By.XPATH, "//*[contains(text(), '목록으로 보기')]")
                list_view_btn.click()
                time.sleep(2)
                print("📋 목록 뷰로 전환")
            except:
                print("⚠️ 이미 목록 뷰이거나 버튼을 찾을 수 없음")

            # 모든 일정 카드 찾기 (data-type="title" 요소들)
            title_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-type="title"]')
            print(f"📌 {len(title_elements)}개 일정 발견")

            for i, title_el in enumerate(title_elements):
                try:
                    # 카드 확장을 위해 부모 요소 클릭
                    card = title_el.find_element(By.XPATH, '../..')
                    card.click()
                    time.sleep(1.5)

                    # 날짜/시간 추출
                    date_el = card.find_element(By.CSS_SELECTOR, '[data-type="date"]')
                    time_el = card.find_element(By.CSS_SELECTOR, '[data-type="time"]')
                    date_text = date_el.text.strip()  # "2월 7일(토)"
                    time_text = time_el.text.strip()  # "14:00 ~ 17:00 (3시간)"

                    # 시작 시간만 추출
                    time_match = re.search(r'(\d{1,2}:\d{2})', time_text)
                    start_time = time_match.group(1) if time_match else ""

                    # 날짜 파싱 (2월 7일 형식)
                    date_match = re.search(r'(\d{1,2})월\s*(\d{1,2})일', date_text)
                    if date_match:
                        month, day = date_match.groups()
                        datetime_str = f"2026년 {month}월 {day}일 {start_time}"
                    else:
                        datetime_str = f"{date_text} {start_time}"

                    class_title = title_el.text.strip()

                    # 장소 추출
                    location_match = re.search(r'\[([^\]]+)\]', class_title)
                    location = location_match.group(1) if location_match else ""

                    # 확장된 카드에서 예약자 정보 추출
                    # 페이지 텍스트에서 이름과 전화번호 패턴 찾기
                    body_text = self.driver.find_element(By.TAG_NAME, 'body').text

                    # 예약자 정보 패턴: "이름 • 010-XXXX-XXXX"
                    participant_pattern = r'([가-힣]{2,4})\s*[•·]\s*(010-?\d{4}-?\d{4})'
                    participants = re.findall(participant_pattern, body_text)

                    if not participants:
                        # 다른 패턴 시도
                        participants = re.findall(r'([가-힣]{2,4})\n•\n(010-?\d{4}-?\d{4})', body_text)

                    for name, phone in participants:
                        # 전화번호 정규화
                        phone = phone.replace('-', '')
                        phone_match = re.search(r'(010\d{8})', phone)
                        if phone_match:
                            phone = phone_match.group(1)

                        reservation = {
                            'platform': '프립',
                            'name': name.strip(),
                            'phone': phone,
                            'people': '1',
                            'datetime': datetime_str,
                            'location': location,
                            'class_title': class_title,
                            'status': '예약 대기'
                        }
                        reservations.append(reservation)
                        print(f"✅ 프립 예약: {name} | {phone} | {datetime_str} | {location}")

                    # 카드 다시 접기 (같은 곳 클릭)
                    card.click()
                    time.sleep(0.5)

                except Exception as e:
                    print(f"⚠️ 일정 {i+1} 처리 실패: {e}")
                    continue
            
            print(f"\n✅ 총 {len(reservations)}개 예약 발견")
            return reservations
            
        except Exception as e:
            print(f"❌ 프립 예약 조회 실패: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def close(self):
        if self.driver:
            self.driver.quit()


# 테스트 코드
if __name__ == "__main__":
    FRIP_EMAIL = "your@email.com"  # 실제 이메일로 변경
    FRIP_PASSWORD = "your_password"  # 실제 비밀번호로 변경
    
    crawler = FripCrawler(FRIP_EMAIL, FRIP_PASSWORD)
    
    try:
        crawler.setup_driver()
        
        if crawler.login():
            reservations = crawler.get_reservations()
            
            print("\n" + "="*50)
            print("📊 크롤링 결과")
            print("="*50)
            
            for res in reservations:
                print(f"""
예약ID: {res['booking_id']}
이름: {res['name']}
전화: {res['phone']}
인원: {res['people']}명
날짜: {res['datetime']}
상태: {res['status']}
""")
    
    finally:
        input("\n아무 키나 누르면 종료됩니다...")
        crawler.close()