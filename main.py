#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 기반 녹취록 자동 요약 및 정리 시스템
메인 실행 파일
"""

import os
import sys
from pathlib import Path
from transcript_summarizer import TranscriptSummarizer

def print_banner():
    """프로그램 배너 출력"""
    print("=" * 60)
    print("    AI 기반 녹취록 자동 요약 및 정리 시스템")
    print("=" * 60)
    print()

def get_api_mode() -> str:
    """API 모드 선택"""
    while True:
        print("API 모드를 선택하세요:")
        print("1. 무료 API (일일 사용량 제한 있음)")
        print("2. 유료 API (더 높은 사용량 제한)")
        print()

        choice = input("선택 (1 또는 2): ").strip()

        if choice == "1":
            return "free"
        elif choice == "2":
            return "paid"
        else:
            print("잘못된 선택입니다. 1 또는 2를 입력하세요.")
            print()

def get_custom_prompt() -> str:
    """사용자 정의 프롬프트 입력받기"""
    print("AI 요약을 위한 프롬프트를 입력하세요.")
    print("(엔터만 누르면 기본 프롬프트 사용)")
    print()

    # 기본 프롬프트 예시 표시
    default_prompt = """너는 뛰어난 회의록 정리자라고 하자. 주어진 txt 파일은 회의 '녹취록'이다. 아주 상세하고도 MECE하게 정리해 주길 부탁한다. 단, 타임스탬프는 제거한다. 단, 테이블로 표현하지 않는다."""

    print("기본 프롬프트 예시:")
    print("-" * 40)
    print(default_prompt)
    print("-" * 40)
    print()

    print("새로운 프롬프트를 입력하세요 (여러 줄 입력 가능, 빈 줄에서 Enter 두 번 누르면 입력 완료):")

    lines = []
    while True:
        line = input()
        if line.strip() == "" and lines and lines[-1].strip() == "":
            # 연속된 빈 줄이면 입력 완료
            lines.pop()  # 마지막 빈 줄 제거
            break
        lines.append(line)

    custom_prompt = "\n".join(lines).strip()

    if not custom_prompt:
        print("기본 프롬프트를 사용합니다.")
        return None
    else:
        print("사용자 정의 프롬프트를 사용합니다.")
        return custom_prompt

def get_input_folder() -> Path:
    """입력 폴더 경로 입력받기"""
    while True:
        print("녹취록 파일이 있는 폴더 경로를 입력하세요.")
        print("예시: C:\\Users\\사용자명\\Documents\\회의록")
        print()

        folder_path = input("입력 폴더 경로: ").strip().strip('"')

        if not folder_path:
            print("경로를 입력해주세요.")
            print()
            continue

        # 경로 정규화
        path = Path(folder_path)

        # 존재 여부 확인
        if not path.exists():
            print(f"오류: 지정된 경로가 존재하지 않습니다: {path}")
            print()
            continue

        # 폴더 여부 확인
        if not path.is_dir():
            print(f"오류: 지정된 경로가 폴더가 아닙니다: {path}")
            print()
            continue

        return path

def get_output_folder(input_folder: Path) -> Path:
    """출력 폴더 경로 입력받기"""
    while True:
        default_output = input_folder / "summarized_results"
        print(f"요약 결과가 저장될 폴더 경로를 입력하세요.")
        print(f"기본값: {default_output}")
        print("(엔터만 누르면 기본값 사용)")
        print()

        folder_path = input("출력 폴더 경로: ").strip().strip('"')

        if not folder_path:
            # 기본값 사용
            path = default_output
        else:
            path = Path(folder_path)

        # 경로 유효성 검사
        try:
            # 부모 디렉토리가 존재하는지 확인
            if path.parent.exists():
                # 쓰기 권한 테스트
                test_file = path / ".test_write_permission"
                test_file.parent.mkdir(parents=True, exist_ok=True)
                test_file.touch()
                test_file.unlink()
                return path
            else:
                print(f"오류: 상위 디렉토리가 존재하지 않습니다: {path.parent}")
                print()
                continue
        except PermissionError:
            print(f"오류: 지정된 경로에 쓰기 권한이 없습니다: {path}")
            print()
            continue
        except Exception as e:
            print(f"오류: 경로 설정 중 문제가 발생했습니다: {e}")
            print()
            continue

def confirm_settings(api_mode: str, input_folder: Path, output_folder: Path, custom_prompt: str):
    """설정 확인"""
    print()
    print("=" * 40)
    print("설정 확인")
    print("=" * 40)
    print(f"API 모드: {'무료' if api_mode == 'free' else '유료'}")
    print(f"입력 폴더: {input_folder}")
    print(f"출력 폴더: {output_folder}")
    print(f"프롬프트: {'사용자 정의' if custom_prompt else '기본'}")
    if custom_prompt:
        print("프롬프트 내용:")
        print("-" * 30)
        print(custom_prompt[:100] + "..." if len(custom_prompt) > 100 else custom_prompt)
        print("-" * 30)
    print("=" * 40)
    print()

    while True:
        confirm = input("위 설정으로 진행하시겠습니까? (y/n): ").strip().lower()

        if confirm in ['y', 'yes', '예']:
            return True
        elif confirm in ['n', 'no', '아니오']:
            return False
        else:
            print("y 또는 n을 입력하세요.")

def main():
    """메인 함수"""
    try:
        # 배너 출력
        print_banner()

        # API 모드 선택
        api_mode = get_api_mode()

        # 사용자 정의 프롬프트 입력
        custom_prompt = get_custom_prompt()

        # 입력 폴더 입력
        input_folder = get_input_folder()

        # 출력 폴더 입력
        output_folder = get_output_folder(input_folder)

        # 설정 확인
        if not confirm_settings(api_mode, input_folder, output_folder, custom_prompt):
            print("작업이 취소되었습니다.")
            return

        print()
        print("작업을 시작합니다...")
        print()

        # TranscriptSummarizer 초기화
        summarizer = TranscriptSummarizer(api_mode, custom_prompt)

        # 폴더 처리
        result = summarizer.process_folder(input_folder, output_folder)

        # 결과 출력
        print()
        print("=" * 40)
        print("작업 완료")
        print("=" * 40)

        if result["success"]:
            print(f"총 파일 수: {result['total']}")
            print(f"성공: {result['processed']}")
            print(f"실패: {result['failed']}")
            print(f"결과 저장 위치: {output_folder}")
        else:
            print(f"오류: {result.get('error', '알 수 없는 오류')}")

        print("=" * 40)

    except KeyboardInterrupt:
        print()
        print("사용자에 의해 작업이 중단되었습니다.")
    except Exception as e:
        print()
        print(f"오류가 발생했습니다: {e}")
        print("자세한 내용은 logs/summary_tool.log 파일을 확인하세요.")

    finally:
        print()
        input("작업이 완료되었습니다. Enter 키를 누르면 창이 닫힙니다.")

if __name__ == "__main__":
    main()
