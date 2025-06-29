import os
import logging
import time
from pathlib import Path
from typing import List, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# API 모드별 설정
API_MODES = {
    'free': {
        'model_name': 'gemini-1.5-flash-latest',
        'delay_seconds': 4,
        'display_name': '무료 API (속도 제한)',
        'env_key_name': 'GOOGLE_API_KEY_FREE'
    },
    'paid': {
        'model_name': 'gemini-2.5-flash-preview-05-20',
        'delay_seconds': 0.2,
        'display_name': '유료 API (최대 속도)',
        'env_key_name': 'GOOGLE_API_KEY_PAID'
    }
}

class TranscriptSummarizer:
    """AI 기반 녹취록 자동 요약 및 정리 시스템"""

    def __init__(self, api_mode: str = "free", custom_prompt: str = None):
        """
        TranscriptSummarizer 초기화

        Args:
            api_mode (str): API 모드 ("free" 또는 "paid")
            custom_prompt (str): 사용자 정의 프롬프트
        """
        if api_mode not in API_MODES:
            raise ValueError(f"지원되지 않는 API 모드입니다: {api_mode}. 지원되는 모드: {list(API_MODES.keys())}")

        self.api_mode = api_mode
        self.mode_config = API_MODES[api_mode]
        self.custom_prompt = custom_prompt
        self.api_key = None
        self.model = None

        # 토큰 사용량 누적을 위한 변수들
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        self.setup_logging()
        self.load_api_key()
        self.initialize_gemini()

    def setup_logging(self):
        """로깅 설정"""
        # logs 디렉토리 생성
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # 로거 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "summary_tool.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_api_key(self):
        """환경 변수에서 API 키 로드"""
        load_dotenv()

        env_key = self.mode_config['env_key_name']
        self.api_key = os.getenv(env_key)

        if not self.api_key:
            raise ValueError(f"{self.mode_config['display_name']} API 키가 .env 파일에 설정되지 않았습니다. 환경 변수명: {env_key}")

    def initialize_gemini(self):
        """Gemini API 초기화"""
        try:
            genai.configure(api_key=self.api_key)
            model_name = self.mode_config['model_name']
            self.model = genai.GenerativeModel(model_name)
            self.logger.info(f"Gemini API 초기화 완료 - 모드: {self.mode_config['display_name']}, 모델: {model_name}")
        except Exception as e:
            self.logger.error(f"Gemini API 초기화 실패: {e}")
            raise

    def check_dependencies(self) -> bool:
        """필수 라이브러리 설치 확인"""
        try:
            import google.generativeai
            import dotenv
            return True
        except ImportError as e:
            self.logger.error(f"필수 라이브러리가 설치되지 않았습니다: {e}")
            print("필수 라이브러리를 설치하려면 다음 명령어를 실행하세요:")
            print("pip install -r requirements.txt")
            return False

    def find_txt_files(self, input_folder: Path) -> List[Path]:
        """
        입력 폴더에서 모든 .txt 파일을 재귀적으로 찾기

        Args:
            input_folder (Path): 검색할 폴더 경로

        Returns:
            List[Path]: 찾은 .txt 파일들의 경로 리스트
        """
        txt_files = []
        try:
            for file_path in input_folder.rglob("*.txt"):
                txt_files.append(file_path)
            self.logger.info(f"총 {len(txt_files)}개의 .txt 파일을 발견했습니다.")
            return txt_files
        except Exception as e:
            self.logger.error(f"파일 검색 중 오류 발생: {e}")
            raise

    def read_file_content(self, file_path: Path) -> str:
        """
        텍스트 파일 내용 읽기 (인코딩 문제 해결)

        Args:
            file_path (Path): 읽을 파일 경로

        Returns:
            str: 파일 내용
        """
        encodings = ['utf-8', 'cp949', 'euc-kr']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                self.logger.debug(f"파일 {file_path}을 {encoding} 인코딩으로 성공적으로 읽었습니다.")
                return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.logger.error(f"파일 읽기 오류 ({file_path}): {e}")
                raise

        raise UnicodeDecodeError(f"파일 {file_path}을 읽을 수 없습니다. 지원되는 인코딩을 모두 시도했습니다.")

    def summarize_text(self, content: str, max_retries: int = 3) -> str:
        """
        AI를 사용하여 텍스트 요약

        Args:
            content (str): 요약할 텍스트 내용
            max_retries (int): 최대 재시도 횟수

        Returns:
            str: 요약된 텍스트
        """
        # 사용자 정의 프롬프트가 있으면 사용, 없으면 기본 프롬프트 사용
        if self.custom_prompt:
            prompt = self.custom_prompt
        else:
            prompt = """너는 뛰어난 회의록 정리자라고 하자. 주어진 txt 파일은 회의 '녹취록'이다. 아주 상세하고도 MECE하게 정리해 주길 부탁한다. 단, 타임스탬프는 제거한다. 단, 테이블로 표현하지 않는다."""

        for attempt in range(max_retries):
            try:
                # API 모드에 따른 딜레이 적용
                if attempt > 0:  # 첫 번째 시도가 아닌 경우에만 딜레이 적용
                    delay_time = self.mode_config['delay_seconds']
                    self.logger.info(f"API 속도 제한을 위해 {delay_time}초 대기 중...")
                    time.sleep(delay_time)

                response = self.model.generate_content(prompt + "\n\n" + content)
                if response.text:
                                        # 토큰 사용량 로깅 및 누적
                    try:
                        if hasattr(response, 'usage_metadata') and response.usage_metadata:
                            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
                            total_tokens = getattr(response.usage_metadata, 'total_token_count', 0)

                            # 토큰 사용량 누적
                            self.total_input_tokens += input_tokens
                            self.total_output_tokens += output_tokens

                            self.logger.info(f"토큰 사용량 - 입력: {input_tokens}, 출력: {output_tokens}, 총합: {total_tokens} (모델: {self.mode_config['model_name']})")
                        else:
                            self.logger.info(f"토큰 사용량 정보를 가져올 수 없습니다. (모델: {self.mode_config['model_name']})")
                    except Exception as token_error:
                        self.logger.warning(f"토큰 사용량 로깅 실패: {token_error}")

                    return response.text
                else:
                    raise Exception("API 응답이 비어있습니다.")

            except Exception as e:
                self.logger.warning(f"API 요청 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # 재시도 시 추가 딜레이 (지수 백오프 + 모드별 기본 딜레이)
                    retry_delay = (2 ** attempt) + self.mode_config['delay_seconds']
                    self.logger.info(f"재시도를 위해 {retry_delay}초 대기 중...")
                    time.sleep(retry_delay)
                else:
                    raise Exception(f"API 요청이 {max_retries}회 시도 후 실패했습니다: {e}")

    def save_summary(self, summary: str, output_path: Path):
        """
        요약 결과를 파일로 저장

        Args:
            summary (str): 저장할 요약 내용
            output_path (Path): 저장할 파일 경로
        """
        try:
            # 출력 디렉토리 생성
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(summary)

            self.logger.info(f"요약 결과 저장 완료: {output_path}")

        except Exception as e:
            self.logger.error(f"파일 저장 오류 ({output_path}): {e}")
            raise

    def process_file(self, input_file: Path, input_folder: Path, output_folder: Path) -> bool:
        """
        단일 파일 처리

        Args:
            input_file (Path): 처리할 입력 파일 경로
            input_folder (Path): 입력 폴더 경로
            output_folder (Path): 출력 폴더 경로

        Returns:
            bool: 처리 성공 여부
        """
        try:
            # 입력 파일의 상대 경로 계산 (입력 폴더 기준)
            relative_path = input_file.relative_to(input_folder)

            # 모델명을 파일명에 포함하기 위해 정리 (특수문자 제거)
            model_name_clean = self.mode_config['model_name'].replace('-', '_').replace('.', '_')

            # 출력 파일 경로 생성 (폴더 구조 유지, 모델명 포함)
            output_file = output_folder / relative_path.parent / f"{input_file.stem}_summary_{model_name_clean}{input_file.suffix}"

            # 파일 내용 읽기
            content = self.read_file_content(input_file)

            # AI 요약
            summary = self.summarize_text(content)

            # 결과 저장
            self.save_summary(summary, output_file)

            return True

        except Exception as e:
            self.logger.error(f"파일 처리 실패 ({input_file}): {e}")
            return False

    def process_folder(self, input_folder: Path, output_folder: Path) -> dict:
        """
        폴더 내 모든 .txt 파일 처리

        Args:
            input_folder (Path): 입력 폴더 경로
            output_folder (Path): 출력 폴더 경로

        Returns:
            dict: 처리 결과 통계
        """
        # 의존성 확인
        if not self.check_dependencies():
            return {"success": False, "error": "필수 라이브러리가 설치되지 않았습니다."}

        # 입력 폴더 유효성 검사
        if not input_folder.exists():
            raise ValueError(f"입력 폴더가 존재하지 않습니다: {input_folder}")

        if not input_folder.is_dir():
            raise ValueError(f"입력 경로가 폴더가 아닙니다: {input_folder}")

        # 출력 폴더 생성
        output_folder.mkdir(parents=True, exist_ok=True)

        # .txt 파일 찾기
        txt_files = self.find_txt_files(input_folder)

        if not txt_files:
            self.logger.warning("처리할 .txt 파일을 찾을 수 없습니다.")
            return {"success": True, "processed": 0, "failed": 0}

        # 파일 처리
        processed_count = 0
        failed_count = 0

        for i, file_path in enumerate(txt_files, 1):
            print(f"파일 처리 중... [{i}/{len(txt_files)}] {file_path.name}")

            if self.process_file(file_path, input_folder, output_folder):
                processed_count += 1
            else:
                failed_count += 1

        result = {
            "success": True,
            "total": len(txt_files),
            "processed": processed_count,
            "failed": failed_count
        }

        # 총 토큰 사용량 로깅
        total_tokens = self.total_input_tokens + self.total_output_tokens
        self.logger.info(f"처리 완료: 총 {len(txt_files)}개, 성공 {processed_count}개, 실패 {failed_count}개")
        self.logger.info(f"전체 토큰 사용량 - 입력: {self.total_input_tokens:,}, 출력: {self.total_output_tokens:,}, 총합: {total_tokens:,} (모델: {self.mode_config['model_name']})")

        return result
