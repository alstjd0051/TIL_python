"""
README.md 생성 스크립트

freeboards 프로젝트 실행 시 README.md에 일자 스케줄을 출력합니다.
- 연도 포함 수강 일자별 상세 내역
- ✅ = 오늘 날짜 표시
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import re


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
        else:  # unrecognized format
            return 0
    except Exception:
        # completely wrong format, return 0 seconds
        return 0


def seconds_to_time(total_seconds: int) -> str:
    """
    초 단위 정수를 "시:분:초" 형식의 문자열로 변환하는 함수.
    """
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"


def parse_korean_date(date_str: str | None) -> datetime | None:
    """
    한국어 날짜 문자열을 datetime 객체로 변환하는 함수.

    예:
    - "12월 22일 (월)" -> 2025-12-22
    - "01월 02일 (금)" -> 2026-01-02

    규칙:
    - 12월  : 2025년
    - 그 외 : 2026년
    """
    if pd.isna(date_str) or date_str == "":
        return None

    try:
        # "12월 22일 (월)" 형식에서 월과 일 추출
        match = re.search(r'(\d+)월\s*(\d+)일', str(date_str))
        if match:
            month = int(match.group(1))
            day = int(match.group(2))

            # 12월은 2025년, 나머지는 2026년으로 매핑
            year = 2025 if month == 12 else 2026

            return datetime(year, month, day)
    except:
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
        # 원래 형식 유지하면서 연도 추가
        return f"{date_obj.year}년 {date_str}"
    return date_str


def load_data(data_path: str | Path | None = None) -> pd.DataFrame:
    """
    CSV 파일을 읽어서 DataFrame으로 반환하는 함수.

    - data_path가 None이면, 현재 스크립트 파일 위치 기준으로
      `asset/schedule.csv` 를 자동으로 찾습니다.
    - 첫 번째 줄(제목 행)은 건너뛰고 둘째 줄을 헤더로 사용합니다.
    """
    if data_path is None:
        # 스크립트 파일의 위치를 기준으로 경로 설정
        script_dir = Path(__file__).parent
        data_path = script_dir / 'asset' / 'schedule.csv'
    else:
        data_path = Path(data_path)

    # CSV 파일 읽기
    # 첫 번째 줄은 제목이므로 건너뛰고, 두 번째 줄을 헤더로 사용
    df = pd.read_csv(data_path, skiprows=1)

    # ❗데이터는 하나도 삭제하지 않고, NaN만 보기 좋게 치환
    # - 전체 NaN을 빈 문자열("")로 바꾸면 테이블에 NaN이 안 보입니다.
    df = df.fillna("")

    return df


def generate_readme_markdown() -> str:
    """
    README.md 마크다운 내용을 생성하는 함수.

    Returns:
        str: README.md 마크다운 내용
    """
    # 데이터 로드
    df = load_data()

    # 클립 시간을 초 단위로 변환
    df['클립 시간'] = df['클립 시간'].replace('', np.nan)
    df['클립 시간(초)'] = df['클립 시간'].apply(time_to_seconds)

    # 일자별 수강 시간을 초로 변환
    df['일자별 수강 시간'] = df['일자별 수강 시간'].replace('', np.nan)
    df['일자별 수강 시간(초)'] = df['일자별 수강 시간'].apply(time_to_seconds)

    # 수강일자에 연도 추가
    df['수강 일자_날짜객체'] = df['수강 일자'].apply(parse_korean_date)
    df['수강 일자_연도포함'] = df['수강 일자'].apply(format_date_with_year)

    # 오늘 날짜 (한국 시간대 기준)
    # GitHub Actions는 UTC를 사용하므로 한국 시간대를 명시적으로 설정
    korea_tz = ZoneInfo("Asia/Seoul")
    today = datetime.now(korea_tz).date()

    # 오늘 날짜와 일치하는 행 확인
    df['오늘_일치'] = df['수강 일자_날짜객체'].apply(
        lambda x: x.date() == today if x is not None else False
    )

    # 수강일자별 클립 시간 재조회 (연도 포함)
    df_date_updated = df[df['수강 일자_날짜객체'].notna()].copy()

    if len(df_date_updated) == 0:
        return "# 수강 일정\n\n⚠️ 수강 일자가 기록된 데이터가 없습니다.\n"

    # 수강 일자별로 클립 시간 합산 (연도 포함된 날짜로 그룹화)
    # 파트명과 클립명은 고유한 값들을 콤마로 구분해서 나열
    def unique_join(series):
        """고유한 값들을 콤마로 구분해서 반환"""
        unique_values = series.dropna().unique()
        unique_values = [str(v).strip() for v in unique_values if str(v).strip() != '']
        return ', '.join(unique_values) if unique_values else ''

    date_summary_updated = df_date_updated.groupby('수강 일자_연도포함').agg({
        '클립 시간(초)': 'sum',
        '일자별 수강 시간(초)': 'first',
        '수강 일자_날짜객체': 'first',
        '파트명': unique_join,
        '클립명': unique_join
    }).reset_index()

    date_summary_updated.columns = ['수강 일자', '클립 시간 합계(초)', '일자별 수강 시간(초)', '날짜객체', '파트명', '클립명']
    date_summary_updated['클립 시간 합계'] = date_summary_updated['클립 시간 합계(초)'].apply(seconds_to_time)
    date_summary_updated['일자별 수강 시간'] = date_summary_updated['일자별 수강 시간(초)'].apply(seconds_to_time)

    # 그룹화 후 오늘 날짜와 일치하는지 다시 확인 (더 안전한 방법)
    date_summary_updated['오늘_일치'] = date_summary_updated['날짜객체'].apply(
        lambda x: x.date() == today if x is not None else False
    )

    # 날짜순으로 정렬
    date_summary_updated = date_summary_updated.sort_values('날짜객체')

    # 전체 합계
    total_clip_seconds = date_summary_updated['클립 시간 합계(초)'].sum()
    total_daily_seconds = date_summary_updated['일자별 수강 시간(초)'].sum()

    # 마크다운 생성
    markdown_lines = [
        "# 수강 일정",
        "",
        f"**업데이트 날짜**: {today.strftime('%Y년 %m월 %d일')}",
        "",
        "## 전체 요약",
        "",
        f"- 수강 일자 수: {len(date_summary_updated)}일",
        f"- 클립 시간 총합: {seconds_to_time(int(total_clip_seconds))}",
        f"- 일자별 수강 시간 총합: {seconds_to_time(int(total_daily_seconds))}",
        "",
        "## 연도 포함 수강 일자별 상세 내역",
        "",
        "| 수강 일자 | 파트명 | 클립명 | 클립 시간 합계 | 일자별 수강 시간 |",
        "|-----------|--------|--------|---------------|----------------|",
    ]

    # 각 일자별 데이터 추가
    for _, row in date_summary_updated.iterrows():
        date_str = row['수강 일자']
        # boolean 값이 확실히 처리되도록 bool()로 변환
        if bool(row['오늘_일치']):
            date_str = f"✅ {date_str}"

        # 파트명과 클립명이 너무 길면 줄임표로 표시
        part_name = str(row['파트명']) if pd.notna(row['파트명']) else ''
        clip_name = str(row['클립명']) if pd.notna(row['클립명']) else ''

        # 마크다운 테이블에서 파이프 문자는 이스케이프 필요 없지만, 줄바꿈은 제거
        part_name = part_name.replace('\n', ' ').replace('|', '\\|')
        clip_name = clip_name.replace('\n', ' ').replace('|', '\\|')

        markdown_lines.append(
            f"| {date_str} | {part_name} | {clip_name} | {row['클립 시간 합계']} | {row['일자별 수강 시간']} |"
        )

    return "\n".join(markdown_lines)


def main() -> None:
    """
    메인 실행 함수.
    README.md 파일을 생성합니다.
    """
    # 프로젝트 루트 디렉토리 찾기 (freeboards의 부모 디렉토리)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    readme_path = project_root / 'README.md'

    # 마크다운 생성
    markdown_content = generate_readme_markdown()

    # README.md 파일 쓰기
    readme_path.write_text(markdown_content, encoding='utf-8')
    print(f"✅ README.md가 생성되었습니다: {readme_path}")


if __name__ == "__main__":
    main()
