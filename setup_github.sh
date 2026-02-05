#!/bin/bash

# 순진무구 자동화 시스템 - GitHub 업로드 스크립트

echo "=================================================="
echo "순진무구 자동화 시스템 - GitHub 설정"
echo "=================================================="
echo ""

# 1. Git 사용자 정보 확인
echo "📝 1단계: Git 사용자 정보 확인"
echo ""

if ! git config --global user.name > /dev/null 2>&1; then
    echo "Git 사용자 이름을 입력하세요:"
    read -p "이름: " git_name
    git config --global user.name "$git_name"
fi

if ! git config --global user.email > /dev/null 2>&1; then
    echo "Git 이메일을 입력하세요:"
    read -p "이메일: " git_email
    git config --global user.email "$git_email"
fi

echo "✅ Git 사용자: $(git config --global user.name) <$(git config --global user.email)>"
echo ""

# 2. Git 초기화
echo "📦 2단계: Git 저장소 초기화"
echo ""

if [ ! -d .git ]; then
    git init
    echo "✅ Git 저장소 초기화 완료"
else
    echo "⚠️ 이미 Git 저장소가 초기화되어 있습니다"
fi
echo ""

# 3. GitHub 저장소 주소 입력
echo "🔗 3단계: GitHub 저장소 연결"
echo ""
echo "GitHub에서 새 저장소를 만드셨나요? (y/n)"
read -p "답변: " created_repo

if [ "$created_repo" != "y" ]; then
    echo ""
    echo "❌ 먼저 GitHub에서 저장소를 만들어주세요!"
    echo ""
    echo "1. https://github.com 로그인"
    echo "2. 우측 상단 + 버튼 → New repository"
    echo "3. Repository name: soonjinmugu-automation"
    echo "4. Private 선택"
    echo "5. Create repository 클릭"
    echo ""
    echo "완료 후 이 스크립트를 다시 실행하세요."
    exit 1
fi

echo ""
echo "GitHub 저장소 주소를 입력하세요:"
echo "예: https://github.com/YOUR_USERNAME/soonjinmugu-automation.git"
read -p "주소: " repo_url

# 기존 remote 제거 (있다면)
git remote remove origin 2>/dev/null

# 새 remote 추가
git remote add origin "$repo_url"
echo "✅ GitHub 저장소 연결 완료"
echo ""

# 4. 파일 추가 및 커밋
echo "📄 4단계: 파일 추가 및 커밋"
echo ""

git add .
git commit -m "순진무구 자동화 시스템 초기 버전"
git branch -M main

echo "✅ 커밋 완료"
echo ""

# 5. GitHub에 업로드
echo "🚀 5단계: GitHub에 업로드"
echo ""
echo "GitHub 로그인 정보를 입력하세요:"
echo "(Password는 Personal Access Token을 사용하세요)"
echo ""

git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "✅ GitHub 업로드 완료!"
    echo "=================================================="
    echo ""
    echo "다음 단계:"
    echo "1. ./setup_secrets.sh 실행 (Secrets 값 준비)"
    echo "2. GitHub 저장소 → Settings → Secrets 설정"
    echo ""
else
    echo ""
    echo "=================================================="
    echo "❌ 업로드 실패"
    echo "=================================================="
    echo ""
    echo "Personal Access Token이 필요합니다:"
    echo "1. GitHub → Settings → Developer settings"
    echo "2. Personal access tokens → Tokens (classic)"
    echo "3. Generate new token (classic)"
    echo "4. repo, workflow 체크"
    echo "5. 생성된 토큰을 Password에 입력"
    echo ""
fi
