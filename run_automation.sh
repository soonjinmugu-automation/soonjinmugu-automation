#!/bin/bash
#
# 순진무구 예약 자동화 실행 스크립트
# launchd에서 매일 오전 9시에 실행
#

# 로그 디렉토리 생성
LOG_DIR="$HOME/자동화/logs"
mkdir -p "$LOG_DIR"

# 로그 파일 (날짜별)
DATE=$(date +%Y%m%d)
LOG_FILE="$LOG_DIR/automation_$DATE.log"

# 작업 디렉토리
WORK_DIR="$HOME/자동화/automation"
cd "$WORK_DIR"

# 로그 시작
echo "========================================" >> "$LOG_FILE"
echo "실행 시작: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 크롬이 실행 중인지 확인
if pgrep -x "Google Chrome" > /dev/null; then
    echo "⚠️ 크롬이 실행 중입니다. 종료 후 다시 시도합니다." >> "$LOG_FILE"
    # 알림 표시 (선택적)
    osascript -e 'display notification "크롬을 종료하고 자동화를 실행해주세요" with title "순진무구 자동화"' 2>/dev/null
    exit 1
fi

# Python 경로 확인 (pyenv 또는 시스템 Python)
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif [ -f "$HOME/.pyenv/shims/python" ]; then
    PYTHON="$HOME/.pyenv/shims/python"
else
    echo "❌ Python을 찾을 수 없습니다." >> "$LOG_FILE"
    exit 1
fi

# 가상환경 활성화 (있는 경우)
if [ -f "$WORK_DIR/venv/bin/activate" ]; then
    source "$WORK_DIR/venv/bin/activate"
    echo "가상환경 활성화됨" >> "$LOG_FILE"
fi

# 메인 스크립트 실행
echo "Python 실행: $PYTHON" >> "$LOG_FILE"
$PYTHON "$WORK_DIR/main.py" >> "$LOG_FILE" 2>&1

# 실행 결과
EXIT_CODE=$?
echo "" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "실행 종료: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "종료 코드: $EXIT_CODE" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 오래된 로그 파일 삭제 (30일 이상)
find "$LOG_DIR" -name "automation_*.log" -mtime +30 -delete

exit $EXIT_CODE
