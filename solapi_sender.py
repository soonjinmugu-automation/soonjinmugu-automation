import requests
import hmac
import hashlib
import time
import uuid
import json
from datetime import datetime

class SolapiSender:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.solapi.com"

    def _get_headers(self):
        """인증 헤더 생성"""
        date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
        salt = str(uuid.uuid4())

        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            (date + salt).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return {
            'Authorization': f'HMAC-SHA256 apiKey={self.api_key}, date={date}, salt={salt}, signature={signature}',
            'Content-Type': 'application/json'
        }

    def send_sms(self, to, text, from_number="01012345678"):
        """SMS 발송"""
        url = f"{self.base_url}/messages/v4/send"

        data = {
            "message": {
                "to": to,
                "from": from_number,
                "text": text
            }
        }

        try:
            response = requests.post(url, headers=self._get_headers(), json=data)
            result = response.json()

            if response.status_code == 200:
                print(f"✅ SMS 발송 성공: {to}")
                return True, result
            else:
                print(f"❌ SMS 발송 실패: {to} - {result}")
                return False, result
        except Exception as e:
            print(f"❌ SMS 발송 오류: {e}")
            return False, str(e)

    def send_mms(self, to, text, image_url=None, from_number="01012345678"):
        """MMS 발송 (이미지 포함)"""
        url = f"{self.base_url}/messages/v4/send"

        message = {
            "to": to,
            "from": from_number,
            "text": text
        }

        if image_url:
            message["imageId"] = image_url  # 이미지 ID 또는 URL

        data = {"message": message}

        try:
            response = requests.post(url, headers=self._get_headers(), json=data)
            result = response.json()

            if response.status_code == 200:
                print(f"✅ MMS 발송 성공: {to}")
                return True, result
            else:
                print(f"❌ MMS 발송 실패: {to} - {result}")
                return False, result
        except Exception as e:
            print(f"❌ MMS 발송 오류: {e}")
            return False, str(e)

    def send_bulk_sms(self, messages, from_number="01012345678"):
        """대량 SMS 발송
        messages: [{'to': '전화번호', 'text': '내용'}, ...]
        """
        url = f"{self.base_url}/messages/v4/send-many"

        data = {
            "messages": [
                {
                    "to": msg['to'],
                    "from": from_number,
                    "text": msg['text']
                }
                for msg in messages
            ]
        }

        try:
            response = requests.post(url, headers=self._get_headers(), json=data)
            result = response.json()

            if response.status_code == 200:
                print(f"✅ 대량 SMS 발송 성공: {len(messages)}건")
                return True, result
            else:
                print(f"❌ 대량 SMS 발송 실패: {result}")
                return False, result
        except Exception as e:
            print(f"❌ 대량 SMS 발송 오류: {e}")
            return False, str(e)

    def get_balance(self):
        """잔액 조회"""
        url = f"{self.base_url}/cash/v1/balance"

        try:
            response = requests.get(url, headers=self._get_headers())
            result = response.json()

            if response.status_code == 200:
                balance = result.get('balance', 0)
                print(f"💰 솔라피 잔액: {balance:,}원")
                return balance
            else:
                print(f"❌ 잔액 조회 실패: {result}")
                return None
        except Exception as e:
            print(f"❌ 잔액 조회 오류: {e}")
            return None


# 테스트
if __name__ == "__main__":
    API_KEY = "NCSEFYUNADFPS4VI"
    API_SECRET = "ECG86DWQEJKD2YGI3CBXDE2AOJRUBB1V"

    sender = SolapiSender(API_KEY, API_SECRET)

    # 잔액 확인
    sender.get_balance()
