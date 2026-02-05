# GitHub Actions 설정 가이드

노트북을 켜두지 않아도 매일 자동으로 크롤링하도록 설정합니다.

---

## ⚡ 빠른 시작 (3단계)

### 1️⃣ token.pickle 생성

```bash
cd /Users/elly/자동화/automation
python3 main.py
```

- 브라우저가 열리면 Google 로그인
- "이 앱은 Google에서 확인하지 않았습니다" → **고급** → **프로젝트로 이동** 클릭
- 권한 허용
- `token.pickle` 파일 자동 생성됨

---

### 2️⃣ GitHub에 업로드

**사전 준비**: GitHub에서 새 저장소 만들기
1. https://github.com 로그인
2. 우측 상단 **+** → **New repository**
3. Repository name: `soonjinmugu-automation`
4. **Private** 선택 (필수!)
5. **Create repository** 클릭

**업로드 실행**:
```bash
cd /Users/elly/자동화/automation
./setup_github.sh
```

스크립트가 단계별로 안내합니다.

**Personal Access Token 필요 시**:
1. GitHub → Settings → Developer settings
2. Personal access tokens → Tokens (classic)
3. Generate new token (classic)
4. `repo`, `workflow` 체크
5. 생성된 토큰을 복사 (비밀번호 대신 사용)

---

### 3️⃣ GitHub Secrets 설정

**Secrets 값 준비**:
```bash
cd /Users/elly/자동화/automation
./setup_secrets.sh
```

스크립트가:
- `credentials.json` → 클립보드에 복사
- `token.pickle` (base64) → 클립보드에 복사
- 모든 값을 `github_secrets.txt`에 저장

**GitHub에 Secrets 추가**:
1. GitHub 저장소 → **Settings** 탭
2. 좌측 **Secrets and variables** → **Actions**
3. **New repository secret** 클릭

**Secret 1**:
```
Name: CREDENTIALS_JSON
Value: (클립보드에 복사된 값 붙여넣기)
```

**Secret 2**:
```
Name: TOKEN_PICKLE_B64
Value: (클립보드에 복사된 값 붙여넣기)
```

---

## ✅ 테스트 실행

1. GitHub 저장소 → **Actions** 탭
2. 좌측 **순진무구 크롤링 자동화** 클릭
3. 우측 **Run workflow** → **Run workflow** 클릭
4. 실행 결과 확인 (녹색 ✓ = 성공)

---

## 🎉 완료!

설정이 완료되면:
- **매일 오전 6시** (한국시간) 자동 실행
- 노트북 꺼도 됨 ✅
- GitHub Actions가 크롤링 → 캘린더/시트 업데이트
- Apps Script가 문자 발송 (기존대로)

---

## 🆘 문제 해결

### token.pickle이 없다고 나옴
→ `python3 main.py` 실행해서 Google 로그인

### git push 실패
→ Personal Access Token 사용 (비밀번호 X)

### Actions 실행 실패
→ Actions 탭에서 빨간 X 클릭 → 오류 로그 확인

---

## 📁 생성된 파일

```
automation/
├── setup_github.sh          # GitHub 업로드 자동화
├── setup_secrets.sh         # Secrets 값 준비
├── github_secrets.txt       # Secrets 백업 (자동 생성)
├── .github/workflows/
│   └── automation.yml       # GitHub Actions 설정
├── .gitignore               # 민감 파일 제외
└── requirements.txt         # Python 패키지 목록
```

---

## 💡 팁

- `github_secrets.txt`는 백업용 (삭제하지 마세요)
- Personal Access Token도 안전한 곳에 보관
- Actions 탭에서 매일 실행 기록 확인 가능
