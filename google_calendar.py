from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
from datetime import datetime, timedelta
import re

SCOPES = ['https://www.googleapis.com/auth/calendar']

# 중복 체크용 캐시 (세션 내에서만 유효)
_existing_events_cache = {}

def get_calendar_service():
    """구글 캘린더 API 서비스"""
    creds = None
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    service = build('calendar', 'v3', credentials=creds)
    return service

def parse_datetime(datetime_str):
    """날짜/시간 문자열 파싱"""
    # 다양한 형식 지원
    patterns = [
        # 2026년 2월 7일 14:00 (공백 포함)
        r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일?\s*(\d{1,2}):(\d{2})',
        # 2026-02-07 14:00
        r'(\d{4})[\-\.](\d{1,2})[\-\.](\d{1,2})\s*(\d{1,2}):(\d{2})',
        # 2월 7일 14:00 (연도 없음)
        r'(\d{1,2})월\s*(\d{1,2})일?\s*(\d{1,2}):(\d{2})',
        # 2/7 14:00
        r'(\d{1,2})[/](\d{1,2})\s*(\d{1,2}):(\d{2})',
    ]

    for pattern in patterns:
        match = re.search(pattern, datetime_str)
        if match:
            groups = match.groups()
            if len(groups) == 5:
                year, month, day, hour, minute = groups
                return datetime(int(year), int(month), int(day), int(hour), int(minute))
            elif len(groups) == 4:
                month, day, hour, minute = groups
                year = datetime.now().year
                return datetime(year, int(month), int(day), int(hour), int(minute))

    return None

def load_events_cache(service, datetime_obj):
    """해당 날짜의 이벤트를 캐시에 로드"""
    global _existing_events_cache
    date_key = datetime_obj.strftime("%Y-%m-%d")

    if date_key not in _existing_events_cache:
        time_min = datetime_obj.replace(hour=0, minute=0, second=0).isoformat() + '+09:00'
        time_max = datetime_obj.replace(hour=23, minute=59, second=59).isoformat() + '+09:00'

        try:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True
            ).execute()
            _existing_events_cache[date_key] = events_result.get('items', [])
        except Exception as e:
            print(f"⚠️ 캘린더 조회 실패: {e}")
            _existing_events_cache[date_key] = []

    return date_key


def find_existing_event(service, datetime_obj, name, phone):
    """기존 일정 찾기 - 이름으로 검색, (이름+전화번호) 또는 (이름+미할당) 매칭"""
    global _existing_events_cache
    date_key = load_events_cache(service, datetime_obj)

    for event in _existing_events_cache[date_key]:
        description = event.get('description', '')
        # 이름이 일치하는 일정 찾기
        if name in description:
            # 완전 일치 (이름 + 전화번호)
            if phone in description:
                return event, 'exact'
            # 미할당 상태인 기존 일정
            if '미할당' in description:
                return event, 'update_phone'
    return None, None


def add_calendar_event(service, reservation, place='센터프라자'):
    """캘린더에 일정 추가 또는 업데이트"""

    datetime_obj = parse_datetime(reservation['datetime'])

    if not datetime_obj:
        print(f"❌ 날짜 파싱 실패: {reservation['datetime']}")
        return None

    name = reservation['name']
    phone = reservation['phone']

    # 기존 일정 확인
    existing_event, match_type = find_existing_event(service, datetime_obj, name, phone)

    if match_type == 'exact':
        # 완전 일치 - 스킵
        print(f'⏭️ 이미 등록됨 (스킵): {name} - {datetime_obj.strftime("%m/%d %H:%M")}')
        return None

    if match_type == 'update_phone' and phone != '미할당':
        # 미할당 → 실제 번호로 업데이트
        try:
            new_description = f"{name}|{phone}|{reservation['people']}|{place}"
            existing_event['description'] = new_description

            updated_event = service.events().update(
                calendarId='primary',
                eventId=existing_event['id'],
                body=existing_event
            ).execute()
            print(f'🔄 전화번호 업데이트: {name} - {datetime_obj.strftime("%m/%d %H:%M")} ({phone})')

            # 캐시 업데이트
            date_key = datetime_obj.strftime("%Y-%m-%d")
            if date_key in _existing_events_cache:
                for i, ev in enumerate(_existing_events_cache[date_key]):
                    if ev.get('id') == existing_event['id']:
                        _existing_events_cache[date_key][i] = updated_event
                        break

            return updated_event
        except Exception as e:
            print(f'❌ 업데이트 실패: {e}')
            return None

    # 새 일정 추가
    start_time = datetime_obj.isoformat()
    end_time = datetime_obj.replace(hour=datetime_obj.hour + 3).isoformat()

    description = f"{name}|{phone}|{reservation['people']}|{place}"

    event = {
        'summary': f"수업 - {reservation['platform']}",
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Asia/Seoul',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Asia/Seoul',
        },
    }

    try:
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print(f'✅ 캘린더 일정 추가: {name} - {datetime_obj.strftime("%m/%d %H:%M")}')

        # 캐시에 새 이벤트 추가
        date_key = datetime_obj.strftime("%Y-%m-%d")
        if date_key in _existing_events_cache:
            _existing_events_cache[date_key].append(created_event)

        return created_event
    except Exception as e:
        print(f'❌ 캘린더 추가 실패: {e}')
        return None