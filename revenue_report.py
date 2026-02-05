"""
월별 매출 CSV 리포트 생성 모듈
"""
import csv
import os
from datetime import datetime
from google_sheets import calculate_revenue, PRICE_PER_PERSON, FRIP_FEE_RATE, SOMSSI_FEE_RATE, LOCATION_RENTAL

OUTPUT_DIR = os.path.expanduser("~/자동화/매출리포트")


def generate_monthly_report(reservations, year=None, month=None):
    """월별 매출 리포트 CSV 생성

    Args:
        reservations: 예약 데이터 리스트
        year: 연도 (기본: 현재 연도)
        month: 월 (기본: 현재 월)

    Returns:
        생성된 CSV 파일 경로
    """
    if not reservations:
        print("📭 리포트 생성할 예약이 없습니다.")
        return None

    now = datetime.now()
    year = year or now.year
    month = month or now.month

    # 출력 폴더 생성
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 파일명
    filename = f"매출리포트_{year}년_{month:02d}월.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # 통계 초기화
    total_price = 0
    total_fee = 0
    total_rental = 0
    total_net = 0
    platform_stats = {'프립': {'count': 0, 'net': 0}, '솜씨당': {'count': 0, 'net': 0}}

    # CSV 작성
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)

        # 헤더
        writer.writerow([
            '날짜', '플랫폼', '수강생 이름', '전화번호', '장소',
            '수업명', '가격', '수수료', '장소대여료', '실수령액'
        ])

        for res in reservations:
            platform = res.get('platform', '')
            location = res.get('location', '')
            people = int(res.get('people', 1))

            # 매출 계산
            price, fee, rental, net = calculate_revenue(platform, location, people)

            # 통계 누적
            total_price += price
            total_fee += fee
            total_rental += rental
            total_net += net

            if platform in platform_stats:
                platform_stats[platform]['count'] += 1
                platform_stats[platform]['net'] += net

            # 행 작성
            writer.writerow([
                res.get('datetime', ''),
                platform,
                res.get('name', ''),
                res.get('phone', ''),
                location,
                res.get('class_title', ''),
                f"{price:,}",
                f"{fee:,}",
                f"{rental:,}",
                f"{net:,}"
            ])

        # 빈 행
        writer.writerow([])

        # 요약 섹션
        writer.writerow(['=' * 10, '월간 요약', '=' * 10])
        writer.writerow([])
        writer.writerow(['총 수강생', f"{len(reservations)}명"])
        writer.writerow(['총 매출', f"{total_price:,}원"])
        writer.writerow(['총 수수료', f"{total_fee:,}원"])
        writer.writerow(['총 장소대여료', f"{total_rental:,}원"])
        writer.writerow(['총 실수령액', f"{total_net:,}원"])
        writer.writerow([])

        # 플랫폼별 통계
        writer.writerow(['플랫폼별 통계'])
        for platform, stats in platform_stats.items():
            if stats['count'] > 0:
                writer.writerow([
                    platform,
                    f"{stats['count']}명",
                    f"실수령 {stats['net']:,}원"
                ])

    print(f"📊 매출 리포트 생성: {filepath}")
    print(f"   총 {len(reservations)}명 | 실수령 {total_net:,}원")

    return filepath


def get_monthly_summary(reservations):
    """월간 요약 정보 반환 (딕셔너리)"""
    if not reservations:
        return None

    total_price = 0
    total_fee = 0
    total_rental = 0
    total_net = 0
    platform_stats = {}

    for res in reservations:
        platform = res.get('platform', '')
        location = res.get('location', '')
        people = int(res.get('people', 1))

        price, fee, rental, net = calculate_revenue(platform, location, people)

        total_price += price
        total_fee += fee
        total_rental += rental
        total_net += net

        if platform not in platform_stats:
            platform_stats[platform] = {'count': 0, 'price': 0, 'fee': 0, 'rental': 0, 'net': 0}

        platform_stats[platform]['count'] += 1
        platform_stats[platform]['price'] += price
        platform_stats[platform]['fee'] += fee
        platform_stats[platform]['rental'] += rental
        platform_stats[platform]['net'] += net

    return {
        'total_count': len(reservations),
        'total_price': total_price,
        'total_fee': total_fee,
        'total_rental': total_rental,
        'total_net': total_net,
        'platform_stats': platform_stats
    }


def print_summary(reservations):
    """매출 요약 출력"""
    summary = get_monthly_summary(reservations)

    if not summary:
        print("📭 요약할 데이터가 없습니다.")
        return

    print("\n" + "=" * 50)
    print("💰 매출 요약")
    print("=" * 50)
    print(f"총 수강생: {summary['total_count']}명")
    print(f"총 매출: {summary['total_price']:,}원")
    print(f"총 수수료: {summary['total_fee']:,}원 (플랫폼)")
    print(f"총 장소대여료: {summary['total_rental']:,}원")
    print(f"실수령액: {summary['total_net']:,}원")
    print()

    print("플랫폼별:")
    for platform, stats in summary['platform_stats'].items():
        print(f"  {platform}: {stats['count']}명 | 실수령 {stats['net']:,}원")
    print("=" * 50)


# 테스트
if __name__ == "__main__":
    # 테스트 데이터
    test_reservations = [
        {
            'datetime': '2026년 2월 7일 14:00',
            'platform': '프립',
            'name': '홍길동',
            'phone': '01012345678',
            'location': '강남',
            'class_title': '[강남] 이모티콘 클래스',
            'people': '1'
        },
        {
            'datetime': '2026년 2월 8일 10:00',
            'platform': '솜씨당',
            'name': '김철수',
            'phone': '01087654321',
            'location': '송파/잠실',
            'class_title': '[송파/잠실] 이모티콘 클래스',
            'people': '1'
        }
    ]

    print_summary(test_reservations)
    generate_monthly_report(test_reservations)
