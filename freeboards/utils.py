"""
공통 유틸리티 모듈

schedule.py와 generate_readme.py에서 공유하는 함수들을 모아놓은 모듈입니다.
- 시간 변환 함수
- 날짜 파싱 함수
- 데이터 로드 함수
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date, datetime
from zoneinfo import ZoneInfo
import re

# 한국 시간대 (GitHub Actions 등 UTC 환경에서도 일관된 시간 보장)
KOREA_TZ = ZoneInfo("Asia/Seoul")


def time_to_seconds(time_str: str | float | int | None) -> int:
    """
    시간 문자열을 초 단위 정수로 변환하는 함수.

    - 지원 형식 예:
      - "0:10:52"  ->  10분 52초  (시:분:초)
      - "12:34"    ->  12분 34초  (분:초)
    """
    if pd.isna(time_str) or time_str == "":
        return 0
    try:
        parts = str(time_str).split(':')
        if len(parts) == 3:  # h:m:s
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # m:s
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:
            return 0
    except (ValueError, TypeError):
        return 0


def seconds_to_time(total_seconds: int) -> str:
    """
    초 단위 정수를 "시:분:초" 형식의 문자열로 변환하는 함수.
    """
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"


def _resolve_year(month: int) -> int:
    """
    월(month)로부터 수강 연도를 동적으로 계산하는 함수.

    커리큘럼은 매년 12월에 시작하여 다음 해 7~8월에 종료되는 구조입니다.
    현재 날짜를 기준으로 적절한 연도를 자동 산출합니다.

    - 현재 8월 이후(9~12월): 12월 -> 올해, 1~8월 -> 내년
    - 현재 8월 이전(1~8월): 12월 -> 작년, 1~8월 -> 올해
    """
    now = datetime.now(KOREA_TZ)
    current_year = now.year
    current_month = now.month

    if current_month >= 9:
        return current_year if month == 12 else current_year + 1
    else:
        return current_year - 1 if month == 12 else current_year


def parse_korean_date(date_str: str | None) -> datetime | None:
    """
    한국어 날짜 문자열을 datetime 객체로 변환하는 함수.

    예:
    - "12월 22일 (월)" -> 2025-12-22
    - "01월 02일 (금)" -> 2026-01-02

    연도는 현재 날짜 기준으로 자동 계산됩니다.
    """
    if pd.isna(date_str) or date_str == "":
        return None

    try:
        match = re.search(r'(\d+)월\s*(\d+)일', str(date_str))
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            year = _resolve_year(month)
            return datetime(year, month, day)
    except (ValueError, TypeError) as e:
        # 잘못된 날짜(예: 2월 30일)나 타입 오류 시 None 반환
        pass
    return None


def format_date_with_year(date_str: str | None) -> str | None:
    """
    날짜 문자열 앞에 연도를 붙여주는 함수.

    예:
    - "12월 22일 (월)" -> "2025년 12월 22일 (월)"
    """
    if pd.isna(date_str) or date_str == "":
        return date_str

    date_obj = parse_korean_date(date_str)
    if date_obj:
        return f"{date_obj.year}년 {date_str}"
    return date_str


def load_data(data_path: str | Path | None = None) -> pd.DataFrame:
    """
    CSV 파일을 읽어서 DataFrame으로 반환하는 함수.

    - data_path가 None이면, 현재 모듈 위치 기준으로
      `asset/schedule.csv` 를 자동으로 찾습니다.
    - 첫 번째 줄(제목 행)은 건너뛰고 둘째 줄을 헤더로 사용합니다.
    """
    if data_path is None:
        script_dir = Path(__file__).parent
        data_path = script_dir / 'asset' / 'schedule.csv'
    else:
        data_path = Path(data_path)

    df = pd.read_csv(data_path, skiprows=1)
    df = df.fillna("")

    return df


def get_today() -> date:
    """한국 시간대 기준 오늘 날짜를 반환하는 함수."""
    return datetime.now(KOREA_TZ).date()
