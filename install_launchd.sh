#!/bin/bash
#
# launchd 서비스 설치/제거 스크립트
#

PLIST_NAME="com.soonjinmugu.automation"
PLIST_SRC="$HOME/자동화/automation/launchd/$PLIST_NAME.plist"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
RUN_SCRIPT="$HOME/자동화/automation/run_automation.sh"

case "$1" in
    install)
        echo "📦 launchd 서비스 설치 중..."

        # 실행 스크립트 권한 설정
        chmod +x "$RUN_SCRIPT"
        echo "✅ 실행 스크립트 권한 설정 완료"

        # 로그 디렉토리 생성
        mkdir -p "$HOME/자동화/logs"
        echo "✅ 로그 디렉토리 생성"

        # 기존 서비스 중지 (있으면)
        launchctl unload "$PLIST_DST" 2>/dev/null

        # plist 파일 복사
        cp "$PLIST_SRC" "$PLIST_DST"
        echo "✅ plist 파일 복사 완료"

        # 서비스 로드
        launchctl load "$PLIST_DST"
        echo "✅ 서비스 로드 완료"

        echo ""
        echo "🎉 설치 완료!"
        echo "   매일 오전 9시에 자동 실행됩니다."
        echo ""
        echo "📋 명령어:"
        echo "   상태 확인: launchctl list | grep soonjinmugu"
        echo "   수동 실행: launchctl start $PLIST_NAME"
        echo "   로그 확인: tail -f ~/자동화/logs/automation.log"
        ;;

    uninstall)
        echo "🗑️ launchd 서비스 제거 중..."

        # 서비스 중지
        launchctl unload "$PLIST_DST" 2>/dev/null

        # plist 파일 삭제
        rm -f "$PLIST_DST"

        echo "✅ 서비스 제거 완료"
        ;;

    status)
        echo "📊 서비스 상태:"
        launchctl list | grep soonjinmugu || echo "   서비스가 로드되지 않았습니다."
        ;;

    run)
        echo "🚀 수동 실행..."
        launchctl start "$PLIST_NAME"
        echo "실행 요청됨. 로그 확인: tail -f ~/자동화/logs/automation.log"
        ;;

    logs)
        echo "📜 최근 로그:"
        tail -50 "$HOME/자동화/logs/automation.log" 2>/dev/null || echo "로그 파일이 없습니다."
        ;;

    *)
        echo "사용법: $0 {install|uninstall|status|run|logs}"
        echo ""
        echo "  install   - 서비스 설치 (매일 오전 9시 실행)"
        echo "  uninstall - 서비스 제거"
        echo "  status    - 서비스 상태 확인"
        echo "  run       - 지금 바로 실행"
        echo "  logs      - 최근 로그 보기"
        exit 1
        ;;
esac
