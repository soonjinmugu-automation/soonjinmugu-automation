"""
순진무구 예약 자동화 시스템
- 프립/솜씨당 크롤링
- 구글 캘린더 등록
- 구글 시트 저장
- 월별 매출 리포트 생성
"""
from frip_crawler import FripCrawler
from somssi_crawler import SomssiCrawler
from google_calendar import get_calendar_service, add_calendar_event
from google_sheets import add_reservation_to_sheet, clear_reservation_cache
from revenue_report import generate_monthly_report, print_summary
import time
import csv
import os
import glob
from datetime import datetime, timedelta

# ========== 설정 ==========
FRIP_EMAIL = "soonjinmugu11@naver.com"
FRIP_PASSWORD = "xntmxkgy0268@"

SOMSSI_EMAIL = "soonjinmugu11@naver.com"
SOMSSI_PASSWORD = "xntmxkgy0268@"

DEFAULT_PLACE = "센터프라자"
OUTPUT_DIR = os.path.expanduser("~/자동화/결과")

# 기능 활성화 설정
ENABLE_GOOGLE_SHEETS = True
ENABLE_GOOGLE_CALENDAR = True
ENABLE_REVENUE_REPORT = True
# ===========================


def cleanup_old_csv(days=7):
    """7일 지난 CSV 파일 삭제"""
    if not os.path.exists(OUTPUT_DIR):
        return

    cutoff_date = datetime.now() - timedelta(days=days)
    deleted_count = 0

    for csv_file in glob.glob(os.path.join(OUTPUT_DIR, "예약_*.csv")):
        file_mtime = datetime.fromtimestamp(os.path.getmtime(csv_file))
        if file_mtime < cutoff_date:
            try:
                os.remove(csv_file)
                deleted_count += 1
            except Exception as e:
                print(f"⚠️ 파일 삭제 실패: {csv_file} - {e}")

    if deleted_count > 0:
        print(f"🗑️ {days}일 지난 CSV 파일 {deleted_count}개 삭제")


def save_results(reservations):
    """결과를 CSV 파일로 저장"""
    if not reservations:
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    cleanup_old_csv(days=7)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(OUTPUT_DIR, f"예약_{timestamp}.csv")

    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['플랫폼', '이름', '전화번호', '일시', '장소', '수업명', '상태'])
        for r in reservations:
            writer.writerow([
                r.get('platform', ''),
                r.get('name', ''),
                r.get('phone', ''),
                r.get('datetime', ''),
                r.get('location', ''),
                r.get('class_title', ''),
                r.get('status', '')
            ])

    print(f"📁 결과 파일 저장: {csv_path}")
    return csv_path


def save_to_google_sheets(reservations):
    """구글 시트에 예약 데이터 저장"""
    if not reservations:
        return

    print("\n📊 구글 시트 저장 중...")

    try:
        added_count = 0
        for res in reservations:
            if add_reservation_to_sheet(res):
                added_count += 1
            time.sleep(0.3)  # API 제한 방지

        print(f"✅ 구글 시트: {added_count}개 추가")
    except Exception as e:
        print(f"⚠️ 구글 시트 저장 실패: {e}")


def save_to_google_calendar(reservations):
    """구글 캘린더에 일정 등록"""
    if not reservations:
        return

    print("\n📅 구글 캘린더 등록 중...")

    try:
        service = get_calendar_service()
        added_count = 0
        updated_count = 0
        skipped_count = 0

        for res in reservations:
            result = add_calendar_event(service, res, DEFAULT_PLACE)
            if result:
                if 'updated' in str(result.get('updated', '')):
                    updated_count += 1
                else:
                    added_count += 1
            else:
                skipped_count += 1
            time.sleep(0.3)

        print(f"✅ 캘린더: {added_count}개 추가, {updated_count}개 업데이트, {skipped_count}개 스킵")

    except FileNotFoundError:
        print("⚠️ credentials.json 파일이 없습니다. 캘린더 연동 스킵")
    except Exception as e:
        print(f"⚠️ 캘린더 등록 실패: {e}")


def main():
    print("=" * 60)
    print("🚀 순진무구 예약 자동화 시작")
    print(f"   실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 캐시 초기화
    clear_reservation_cache()

    all_reservations = []

    # 1. 프립 크롤링
    print("\n" + "=" * 50)
    print("1️⃣ 프립 크롤링")
    print("=" * 50)

    frip = FripCrawler(FRIP_EMAIL, FRIP_PASSWORD)

    try:
        # GitHub Actions 환경에서는 Chrome Profile 사용 안 함
        use_profile = os.getenv('CI') != 'true'
        driver = frip.setup_driver(use_profile=use_profile)

        if frip.login():
            frip_reservations = frip.get_reservations()
            all_reservations.extend(frip_reservations)
            print(f"✅ 프립: {len(frip_reservations)}개 예약 발견")

        # 2. 솜씨당 크롤링 (같은 브라우저 사용)
        print("\n" + "=" * 50)
        print("2️⃣ 솜씨당 크롤링")
        print("=" * 50)

        somssi = SomssiCrawler(SOMSSI_EMAIL, SOMSSI_PASSWORD)
        somssi.driver = driver

        if somssi.login():
            somssi_reservations = somssi.get_reservations()
            all_reservations.extend(somssi_reservations)
            print(f"✅ 솜씨당: {len(somssi_reservations)}개 예약 발견")

    except Exception as e:
        print(f"❌ 크롤링 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        frip.close()

    # 결과 처리
    if all_reservations:
        print(f"\n📋 총 {len(all_reservations)}개 예약 수집 완료")

        # 3. CSV 파일 저장
        print("\n" + "=" * 50)
        print("3️⃣ 결과 파일 저장")
        print("=" * 50)
        save_results(all_reservations)

        # 4. 구글 캘린더 등록
        if ENABLE_GOOGLE_CALENDAR:
            print("\n" + "=" * 50)
            print("4️⃣ 구글 캘린더 등록")
            print("=" * 50)
            save_to_google_calendar(all_reservations)

        # 5. 구글 시트 저장
        if ENABLE_GOOGLE_SHEETS:
            print("\n" + "=" * 50)
            print("5️⃣ 구글 시트 저장")
            print("=" * 50)
            save_to_google_sheets(all_reservations)

        # 6. 매출 요약 출력
        if ENABLE_REVENUE_REPORT:
            print_summary(all_reservations)

    else:
        print("\n📭 새로운 예약이 없습니다.")

    print("\n" + "=" * 60)
    print("🔚 자동화 종료")
    print(f"   종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


def generate_report():
    """매출 리포트 생성 (별도 실행용)"""
    from google_sheets import get_sheet_data

    print("📊 월간 매출 리포트 생성")

    # 구글 시트에서 이번 달 예약 데이터 가져오기
    try:
        data = get_sheet_data("예약")
        if not data:
            print("❌ 시트 데이터를 가져올 수 없습니다.")
            return

        # 헤더 제외
        reservations = []
        for row in data[1:]:
            if len(row) >= 6:
                reservations.append({
                    'datetime': row[0],
                    'platform': row[1],
                    'name': row[2],
                    'phone': row[3],
                    'location': row[4],
                    'class_title': row[5],
                    'people': '1'
                })

        if reservations:
            generate_monthly_report(reservations)
        else:
            print("📭 리포트 생성할 데이터가 없습니다.")

    except Exception as e:
        print(f"❌ 리포트 생성 실패: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "report":
        generate_report()
    else:
        main()
