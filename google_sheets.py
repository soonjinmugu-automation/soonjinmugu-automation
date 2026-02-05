from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
import re
from datetime import datetime

# 중복 체크용 캐시
_existing_reservations_cache = None

# 구글 시트 + 캘린더 권한
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/calendar'
]

# 스프레드시트 ID
SPREADSHEET_ID = "1Y4g08k3y3CY2NDaGgFyvTC1t1QQOVXU8PE-jEYZGgKA"

# 수업 완료 기록용 스프레드시트 ID
ARCHIVE_SPREADSHEET_ID = "1GE0Ge7TY_Zzgkbm2tXYpdx_NKrF15M2nq3S2FVeqWW4"

# 가격 설정
PRICE_PER_PERSON = 85000
FRIP_FEE_RATE = 0.189  # 18.9%
SOMSSI_FEE_RATE = 0.18  # 18%

# 장소 대여료
LOCATION_RENTAL = {
    "포커스": 12000,  # 인당
    "시디즈": 0,
    "강남": 12000,  # 포커스로 가정
    "송파/잠실": 0,  # 시디즈로 가정
}


def get_sheets_service():
    """구글 시트 API 서비스 반환"""
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    return service


def get_sheet_data(sheet_name, range_notation="A:Z"):
    """시트에서 데이터 읽기"""
    service = get_sheets_service()
    range_full = f"{sheet_name}!{range_notation}"

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_full
        ).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"❌ 시트 읽기 실패: {e}")
        return []


def append_to_sheet(sheet_name, values):
    """시트에 데이터 추가 (맨 아래에)"""
    service = get_sheets_service()
    range_full = f"{sheet_name}!A:Z"

    body = {'values': values}

    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=range_full,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        print(f"✅ 시트 데이터 추가: {len(values)}행")
        return True
    except Exception as e:
        print(f"❌ 시트 추가 실패: {e}")
        return False


def update_cell(sheet_name, cell, value):
    """특정 셀 업데이트"""
    service = get_sheets_service()
    range_full = f"{sheet_name}!{cell}"

    body = {'values': [[value]]}

    try:
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_full,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        return True
    except Exception as e:
        print(f"❌ 셀 업데이트 실패: {e}")
        return False


def calculate_revenue(platform, location, people_count=1):
    """매출 계산
    Returns: (가격, 수수료, 장소대여료, 실수령액)
    """
    price = PRICE_PER_PERSON * people_count

    # 플랫폼 수수료
    if platform == "프립":
        fee_rate = FRIP_FEE_RATE
    else:  # 솜씨당
        fee_rate = SOMSSI_FEE_RATE

    fee = int(price * fee_rate)

    # 장소 대여료
    rental = 0
    for loc_key, loc_fee in LOCATION_RENTAL.items():
        if loc_key in location:
            rental = loc_fee * people_count
            break

    net_revenue = price - fee - rental

    return price, fee, rental, net_revenue


def parse_datetime_for_sheet(datetime_str):
    """날짜/시간 문자열을 시트용 포맷으로 변환

    Returns: (날짜 문자열, 수업시간 문자열)
    예: ("26년 2월 7일", "14시-17시")
    """
    # 날짜 추출 패턴들
    patterns = [
        # 2026년 2월 7일 14:00
        r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일?\s*(\d{1,2}):(\d{2})',
        # 2026-02-07 14:00
        r'(\d{4})[-.](\d{1,2})[-.](\d{1,2})\s*(\d{1,2}):(\d{2})',
    ]

    for pattern in patterns:
        match = re.search(pattern, datetime_str)
        if match:
            year, month, day, hour, minute = match.groups()
            year_short = str(int(year))[-2:]  # 2026 -> 26
            date_str = f"{year_short}년 {int(month)}월 {int(day)}일"

            # 수업 시간 (3시간 기준)
            start_hour = int(hour)
            end_hour = start_hour + 3
            time_str = f"{start_hour}시-{end_hour}시"

            return date_str, time_str

    # 파싱 실패 시 원본 반환
    return datetime_str, ""


def load_existing_reservations(sheet_name="예약목록"):
    """기존 예약 데이터 캐시 로드

    새 컬럼 구조:
    A(0): 일자, B(1): 수업시간, C(2): 플랫폼, D(3): 이름, E(4): 전화번호
    """
    global _existing_reservations_cache

    if _existing_reservations_cache is None:
        data = get_sheet_data(sheet_name)
        _existing_reservations_cache = set()

        for row in data[1:]:  # 헤더 제외
            if len(row) >= 5:
                # 날짜 + 이름 + 전화번호로 고유 키 생성
                date = row[0] if row[0] else ""
                name = row[3] if len(row) > 3 else ""  # D열: 이름
                phone = row[4] if len(row) > 4 else ""  # E열: 전화번호
                key = f"{date}|{name}|{phone}"
                _existing_reservations_cache.add(key)

    return _existing_reservations_cache


def is_duplicate_reservation(date_str, name, phone, sheet_name="예약목록"):
    """중복 예약인지 확인"""
    existing = load_existing_reservations(sheet_name)
    key = f"{date_str}|{name}|{phone}"
    return key in existing


def add_to_cache(date_str, name, phone):
    """캐시에 새 예약 추가"""
    global _existing_reservations_cache
    if _existing_reservations_cache is not None:
        key = f"{date_str}|{name}|{phone}"
        _existing_reservations_cache.add(key)


def add_reservation_to_sheet(reservation, sheet_name="예약목록"):
    """예약 데이터를 시트에 추가 (중복 체크 포함)"""

    # 날짜/시간 분리
    date_str, time_str = parse_datetime_for_sheet(reservation.get('datetime', ''))
    name = reservation.get('name', '')
    phone = reservation.get('phone', '')

    # 중복 체크
    if is_duplicate_reservation(date_str, name, phone, sheet_name):
        print(f"⏭️ 시트 중복 스킵: {name} - {date_str}")
        return False

    # 매출 계산
    price, fee, rental, net = calculate_revenue(
        reservation['platform'],
        reservation.get('location', ''),
        int(reservation.get('people', 1))
    )

    row = [
        date_str,  # 일자 (26년 2월 7일)
        time_str,  # 수업시간 (14시-17시)
        reservation.get('platform', ''),  # 플랫폼
        name,  # 이름
        phone,  # 전화번호
        reservation.get('location', ''),  # 장소
        reservation.get('class_title', ''),  # 수업명
        price,  # 가격
        fee,  # 수수료
        rental,  # 장소대여료
        net,  # 실수령액
        reservation.get('status', ''),  # 상태
        '',  # 7일전 문자
        '',  # 당일 문자
        '',  # 종료 문자
    ]

    result = append_to_sheet(sheet_name, [row])

    if result:
        # 캐시에 추가
        add_to_cache(date_str, name, phone)

    return result


def get_message_template(template_name, sheet_name="문자템플릿"):
    """문자 템플릿 가져오기"""
    data = get_sheet_data(sheet_name)

    for row in data:
        if len(row) >= 2 and row[0] == template_name:
            return row[1]

    return None


def get_reservations_for_date(target_date, sheet_name="예약목록"):
    """특정 날짜의 예약 목록 가져오기

    새 컬럼 구조:
    A: 일자, B: 수업시간, C: 플랫폼, D: 이름, E: 전화번호, F: 장소, G: 수업명
    """
    data = get_sheet_data(sheet_name)
    reservations = []

    for row in data[1:]:  # 헤더 제외
        if len(row) >= 5:
            date_str = row[0]  # 일자
            if target_date in date_str:
                reservations.append({
                    'date': row[0],  # 일자
                    'time': row[1] if len(row) > 1 else '',  # 수업시간
                    'platform': row[2] if len(row) > 2 else '',
                    'name': row[3] if len(row) > 3 else '',
                    'phone': row[4] if len(row) > 4 else '',
                    'location': row[5] if len(row) > 5 else '',
                    'class_title': row[6] if len(row) > 6 else '',
                })

    return reservations


def clear_reservation_cache():
    """예약 캐시 초기화 (새 세션 시작 시 호출)"""
    global _existing_reservations_cache
    _existing_reservations_cache = None


def archive_completed_class(reservation, sheet_name="완료"):
    """수업 완료 데이터를 별도 스프레드시트에 저장

    Args:
        reservation: 예약 데이터 딕셔너리
        sheet_name: 저장할 시트 이름 (기본: "완료")
    """
    service = get_sheets_service()

    # 날짜/시간 분리
    date_str, time_str = parse_datetime_for_sheet(reservation.get('datetime', ''))

    # 매출 계산
    price, fee, rental, net = calculate_revenue(
        reservation.get('platform', ''),
        reservation.get('location', ''),
        int(reservation.get('people', 1))
    )

    row = [
        date_str,  # 일자
        time_str,  # 수업시간
        reservation.get('platform', ''),  # 플랫폼
        reservation.get('name', ''),  # 이름
        reservation.get('phone', ''),  # 전화번호
        reservation.get('location', ''),  # 장소
        reservation.get('class_title', ''),  # 수업명
        price,  # 가격
        fee,  # 수수료
        rental,  # 장소대여료
        net,  # 실수령액
        datetime.now().strftime("%Y-%m-%d %H:%M"),  # 기록 시간
    ]

    body = {'values': [row]}

    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=ARCHIVE_SPREADSHEET_ID,
            range=f"{sheet_name}!A:L",
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        print(f"📁 완료 기록 저장: {reservation.get('name', '')} - {date_str}")
        return True
    except Exception as e:
        print(f"❌ 완료 기록 저장 실패: {e}")
        return False


def get_archive_sheet_data(sheet_name="완료", range_notation="A:L"):
    """완료 기록 시트에서 데이터 읽기"""
    service = get_sheets_service()
    range_full = f"{sheet_name}!{range_notation}"

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=ARCHIVE_SPREADSHEET_ID,
            range=range_full
        ).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"❌ 완료 기록 읽기 실패: {e}")
        return []


# 테스트
if __name__ == "__main__":
    print("📊 구글 시트 연동 테스트")

    # 시트 목록 확인
    try:
        service = get_sheets_service()
        sheet_metadata = service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()
        sheets = sheet_metadata.get('sheets', [])
        print("\n📑 시트 목록:")
        for sheet in sheets:
            print(f"  - {sheet['properties']['title']}")
    except Exception as e:
        print(f"❌ 시트 접근 실패: {e}")
        print("   credentials.json과 token.pickle 확인 필요")
