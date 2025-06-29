# AI 기반 녹취록 자동 요약 및 정리 시스템

Google Gemini AI를 활용하여 회의, 인터뷰, 강의 등의 녹취록을 자동으로 요약하고 정리하는 CLI 도구입니다.

## 주요 기능

- **자동 파일 탐색**: 지정된 폴더와 하위 폴더의 모든 `.txt` 파일을 재귀적으로 탐색
- **AI 기반 요약**: Google Gemini API를 사용한 고품질 요약 생성
- **구조화된 출력**: MECE 원칙에 따른 체계적인 요약본 생성
- **폴더 구조 유지**: 원본 폴더 구조를 그대로 유지하여 결과 저장
- **사용자 친화적 CLI**: 직관적인 대화형 인터페이스

## 시스템 요구사항

- Windows 10/11
- Python 3.7 이상
- 인터넷 연결
- Google Gemini API 키

## 설치 방법

### 1. 저장소 클론 또는 다운로드

```bash
git clone <repository-url>
cd TranscriptSummarizerAI
```

### 2. Python 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. API 키 설정

1. `env_example.txt` 파일을 `.env`로 복사합니다.
2. `.env` 파일을 편집하여 Google Gemini API 키를 설정합니다:

```env
# Google Gemini API Keys
GOOGLE_API_KEY_FREE="your_free_api_key_here"
GOOGLE_API_KEY_PAID="your_paid_api_key_here"
```

#### Google Gemini API 키 발급 방법

1. [Google AI Studio](https://makersuite.google.com/app/apikey)에 접속
2. Google 계정으로 로그인
3. "Create API Key" 클릭
4. 생성된 API 키를 복사하여 `.env` 파일에 붙여넣기

## 사용 방법

### 1. 프로그램 실행

```bash
python main.py
```

### 2. 설정 입력

프로그램이 실행되면 다음 정보를 순차적으로 입력합니다:

1. **API 모드 선택**
   - 무료 API (일일 사용량 제한 있음)
   - 유료 API (더 높은 사용량 제한)

2. **입력 폴더 경로**
   - 녹취록 `.txt` 파일이 있는 폴더 경로 입력
   - 예: `C:\Users\사용자명\Documents\회의록`

3. **출력 폴더 경로**
   - 요약 결과가 저장될 폴더 경로 입력
   - 기본값: `[입력폴더]\summarized_results`
   - 엔터만 누르면 기본값 사용

4. **설정 확인**
   - 입력한 설정을 확인하고 실행 여부 결정

### 3. 결과 확인

- 처리된 파일 수, 성공/실패 개수가 표시됩니다
- 요약된 파일은 `[원본파일명]_summary.txt` 형식으로 저장됩니다
- 원본 폴더 구조가 그대로 유지됩니다

## 파일 구조 예시

### 입력 폴더 구조
```
C:\회의록\
├── 프로젝트A\
│   ├── 기획회의.txt
│   └── 개발회의.txt
└── 프로젝트B\
    └── 리뷰회의.txt
```

### 출력 폴더 구조
```
C:\회의록\summarized_results\
├── 프로젝트A\
│   ├── 기획회의_summary.txt
│   └── 개발회의_summary.txt
└── 프로젝트B\
    └── 리뷰회의_summary.txt
```

## 로그 및 오류 처리

- 모든 작업 로그는 `logs/summary_tool.log` 파일에 저장됩니다
- API 요청 실패 시 최대 3회까지 자동 재시도합니다
- 파일 인코딩 문제 시 UTF-8, CP949, EUC-KR 순으로 시도합니다

## 주의사항

1. **API 사용량**: 무료 API는 일일 사용량 제한이 있습니다
2. **파일 크기**: 개별 파일이 Gemini API의 토큰 제한을 초과하지 않도록 주의하세요
3. **인터넷 연결**: 안정적인 인터넷 연결이 필요합니다
4. **파일 형식**: 현재 `.txt` 파일만 지원합니다

## 문제 해결

### 일반적인 오류

1. **"필수 라이브러리가 설치되지 않았습니다"**
   ```bash
   pip install -r requirements.txt
   ```

2. **"API 키가 .env 파일에 설정되지 않았습니다"**
   - `.env` 파일이 프로젝트 루트에 있는지 확인
   - API 키가 올바르게 설정되었는지 확인

3. **"지정된 경로가 존재하지 않습니다"**
   - 입력한 폴더 경로가 정확한지 확인
   - 경로에 특수문자가 포함된 경우 따옴표로 감싸기

4. **"쓰기 권한이 없습니다"**
   - 출력 폴더에 대한 쓰기 권한 확인
   - 관리자 권한으로 실행 시도

### 로그 확인

자세한 오류 정보는 `logs/summary_tool.log` 파일을 확인하세요.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 지원

문제가 발생하거나 개선 사항이 있으시면 이슈를 등록해 주세요.
