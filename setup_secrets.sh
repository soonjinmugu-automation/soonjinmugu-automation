#!/bin/bash

# 순진무구 자동화 시스템 - GitHub Secrets 준비 스크립트

echo "=================================================="
echo "GitHub Secrets 값 준비"
echo "=================================================="
echo ""

# 결과를 저장할 파일
OUTPUT_FILE="github_secrets.txt"
rm -f "$OUTPUT_FILE"

echo "🔐 GitHub Secrets에 추가할 값들을 준비합니다..."
echo ""

# 1. CREDENTIALS_JSON 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Secret 1: CREDENTIALS_JSON"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "credentials.json" ]; then
    echo "✅ credentials.json 파일 발견"
    echo ""
    echo "Name: CREDENTIALS_JSON" >> "$OUTPUT_FILE"
    echo "Value:" >> "$OUTPUT_FILE"
    cat credentials.json >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    # 클립보드에 복사
    cat credentials.json | pbcopy
    echo "✅ credentials.json 내용이 클립보드에 복사되었습니다"
    echo "   → GitHub Secrets에 CREDENTIALS_JSON 이름으로 붙여넣으세요"
else
    echo "❌ credentials.json 파일이 없습니다!"
    echo "   Google Cloud Console에서 다운로드하세요."
fi

echo ""
echo "계속하려면 Enter를 누르세요..."
read

# 2. TOKEN_PICKLE_B64 확인
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Secret 2: TOKEN_PICKLE_B64"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "token.pickle" ]; then
    echo "✅ token.pickle 파일 발견"
    echo ""
    echo "Name: TOKEN_PICKLE_B64" >> "$OUTPUT_FILE"
    echo "Value:" >> "$OUTPUT_FILE"
    base64 -i token.pickle >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    # 클립보드에 복사
    base64 -i token.pickle | pbcopy
    echo "✅ token.pickle (base64) 내용이 클립보드에 복사되었습니다"
    echo "   → GitHub Secrets에 TOKEN_PICKLE_B64 이름으로 붙여넣으세요"
else
    echo "❌ token.pickle 파일이 없습니다!"
    echo ""
    echo "먼저 token.pickle을 생성해야 합니다:"
    echo "1. python3 main.py 실행"
    echo "2. 브라우저에서 Google 로그인"
    echo "3. token.pickle 자동 생성"
    echo ""
    echo "token.pickle 생성 후 이 스크립트를 다시 실행하세요."
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ Secrets 준비 완료!"
echo "=================================================="
echo ""
echo "📋 모든 값이 '$OUTPUT_FILE' 파일에 저장되었습니다"
echo ""
echo "다음 단계:"
echo "1. GitHub 저장소 → Settings → Secrets and variables → Actions"
echo "2. New repository secret 클릭"
echo "3. 아래 순서대로 2개 Secret 추가:"
echo ""
echo "   Secret 1:"
echo "   - Name: CREDENTIALS_JSON"
echo "   - Value: (위에서 클립보드에 복사된 값 붙여넣기)"
echo ""
echo "   Secret 2:"
echo "   - Name: TOKEN_PICKLE_B64"
echo "   - Value: (위에서 클립보드에 복사된 값 붙여넣기)"
echo ""
echo "=================================================="
