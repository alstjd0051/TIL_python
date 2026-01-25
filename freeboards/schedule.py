"""
수강 일정 데이터 분석 스크립트

- `asset/schedule.csv` 파일을 읽어서
  - 전체/강의별/파트별 클립 시간 요약
  - 수강 일자별(연도 포함) 시간 요약
  - 오늘 날짜와 겹치는 수강 기록
  을 터미널에서 예쁘게 출력합니다.

- 이 파일의 핵심 로직은 노트북 `time.ipynb` 에도 동일하게 옮겨서 사용할 수 있습니다.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import re

from rich.console import Console
from rich.table import Table

# 터미널용 콘솔 객체 (색상/테이블 출력 담당)
console = Console()


def print_rich_table(df: pd.DataFrame, title: str | None = None, max_rows: int = 30) -> None:
    """
    DataFrame을 터미널에서 예쁘게 출력하기 위한 헬퍼 함수.

    - 컬럼명을 rich Table 헤더로 사용
    - 앞에서부터 최대 max_rows 행까지만 출력
    """
    if df is None or df.empty:
        console.print(f"[bold red]{title or '테이블'}[/bold red] - 표시할 데이터가 없습니다.")
        return

    table = Table(title=title, show_lines=True)

    # DataFrame 컬럼명을 테이블 헤더로 추가
    for col in df.columns:
        table.add_column(str(col))

    # 각 행을 문자열로 변환하여 테이블에 추가
    for _, row in df.head(max_rows).iterrows():
        table.add_row(*[str(v) for v in row.values])

    console.print(table)


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
        if len(parts) == 3:  # 시:분:초
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # 분:초
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:  # 인식할 수 없는 형식
            return 0
    except Exception:
        # 형식이 완전히 잘못된 경우 0초로 처리
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


def analyze_clip_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    클립 시간 관련 통계를 계산하고 출력하는 함수.

    - 전체 클립 개수 / 총 시간 / 평균 시간
    - 강의별 클립 시간 요약
    - 파트별 클립 시간 요약
    """
    # 클립 시간 데이터 처리
    # 빈 문자열을 NaN으로 다시 변환 (계산을 위해)
    df_time = df.copy()
    df_time['클립 시간'] = df_time['클립 시간'].replace('', np.nan)

    # 클립 시간을 초 단위로 변환
    df_time['클립 시간(초)'] = df_time['클립 시간'].apply(time_to_seconds)

    # 전체 클립 시간 합산
    total_seconds = df_time['클립 시간(초)'].sum()
    total_time_str = seconds_to_time(total_seconds)

    print("=" * 60)
    print("📊 클립 시간 종합 분석")
    print("=" * 60)
    print(f"\n✅ 전체 클립 개수: {len(df_time)}개")
    print(f"✅ 클립 시간이 있는 데이터: {df_time['클립 시간(초)'].notna().sum()}개")
    print(f"✅ 총 클립 시간: {total_time_str} ({total_seconds:,}초)")
    print(f"✅ 평균 클립 시간: {seconds_to_time(int(df_time['클립 시간(초)'].mean()))}")

    # 강의별 클립 시간 합산
    if '강의명' in df_time.columns:
        lecture_summary = df_time.groupby('강의명')['클립 시간(초)'].agg(['sum', 'count', 'mean']).reset_index()
        lecture_summary.columns = ['강의명', '총 시간(초)', '클립 개수', '평균 시간(초)']
        lecture_summary['총 시간'] = lecture_summary['총 시간(초)'].apply(seconds_to_time)
        lecture_summary['평균 시간'] = lecture_summary['평균 시간(초)'].apply(lambda x: seconds_to_time(int(x)) if pd.notna(x) else "0:00:00")

        print(f"\n📚 강의별 클립 시간 요약:")
        print("-" * 60)
        print_rich_table(
            lecture_summary[['강의명', '클립 개수', '총 시간', '평균 시간']],
            title="강의별 클립 시간 요약"
        )

    # 파트별 클립 시간 합산
    if '파트명' in df_time.columns:
        part_summary = df_time.groupby('파트명')['클립 시간(초)'].agg(['sum', 'count']).reset_index()
        part_summary.columns = ['파트명', '총 시간(초)', '클립 개수']
        part_summary['총 시간'] = part_summary['총 시간(초)'].apply(seconds_to_time)
        part_summary = part_summary.sort_values('총 시간(초)', ascending=False)

        print(f"\n📖 파트별 클립 시간 요약:")
        print("-" * 60)
        print_rich_table(
            part_summary[['파트명', '클립 개수', '총 시간']].head(10),
            title="파트별 클립 시간 요약 (상위 10개)"
        )

    return df_time


def analyze_by_date(df_time: pd.DataFrame) -> None:
    """
    수강 일자(월/일) 기준으로 클립 시간을 집계하는 함수.

    - 일자별 클립 시간 합계 vs 일자별 수강 시간 합계
    - 일자별 차이(초)와 비고(어느 쪽이 더 큰지) 출력
    """
    # 수강 일자가 있는 데이터만 필터링
    df_date = df_time[df_time['수강 일자'] != ''].copy()

    if len(df_date) > 0:
        # 일자별 수강 시간도 초로 변환
        df_date['일자별 수강 시간(초)'] = df_date['일자별 수강 시간'].apply(time_to_seconds)

        date_summary_with_daily = df_date.groupby('수강 일자').agg({
            '클립 시간(초)': 'sum',
            '일자별 수강 시간(초)': 'first',  # 같은 날짜면 같은 값이므로 first 사용
            '클립명': 'count'
        }).reset_index()

        date_summary_with_daily.columns = ['수강 일자', '클립 시간 합계(초)', '일자별 수강 시간(초)', '클립 개수']
        date_summary_with_daily['클립 시간 합계'] = date_summary_with_daily['클립 시간 합계(초)'].apply(seconds_to_time)
        date_summary_with_daily['일자별 수강 시간'] = date_summary_with_daily['일자별 수강 시간(초)'].apply(seconds_to_time)

        print("=" * 80)
        print("📅 수강 일자별 클립 시간 종합 정리")
        print("=" * 80)
        print(f"\n✅ 수강 일자가 기록된 데이터: {len(df_date)}개")
        print(f"✅ 수강 일자 수: {len(date_summary_with_daily)}일")

        # 전체 합계
        total_clip_seconds = date_summary_with_daily['클립 시간 합계(초)'].sum()
        total_daily_seconds = date_summary_with_daily['일자별 수강 시간(초)'].sum()

        print(f"\n📊 전체 요약:")
        print(f"   - 클립 시간 총합: {seconds_to_time(int(total_clip_seconds))}")
        print(f"   - 일자별 수강 시간 총합: {seconds_to_time(int(total_daily_seconds))}")

        print(f"\n📅 일자별 상세 내역:")
        print("-" * 80)
        detail_df = date_summary_with_daily[['수강 일자', '클립 개수', '클립 시간 합계', '일자별 수강 시간']].sort_values('수강 일자')
        print_rich_table(detail_df, title="수강 일자별 상세 내역")

        # 일자별 수강 시간과 클립 시간 합계 비교
        print(f"\n📈 일자별 수강 시간 vs 클립 시간 합계 비교:")
        print("-" * 80)
        comparison = date_summary_with_daily.copy()
        comparison['차이(초)'] = comparison['일자별 수강 시간(초)'] - comparison['클립 시간 합계(초)']
        comparison['차이'] = comparison['차이(초)'].apply(lambda x: seconds_to_time(int(abs(x))) if pd.notna(x) else "")
        comparison['비고'] = comparison.apply(
            lambda row: "일자별 시간이 더 많음" if row['차이(초)'] > 0
            else "클립 시간 합계가 더 많음" if row['차이(초)'] < 0
            else "동일", axis=1
        )
        comp_df = comparison[['수강 일자', '클립 시간 합계', '일자별 수강 시간', '차이', '비고']].sort_values('수강 일자')
        print_rich_table(comp_df, title="일자별 수강 시간 vs 클립 시간 합계 비교")
    else:
        print("⚠️ 수강 일자가 기록된 데이터가 없습니다.")


def analyze_by_date_with_year(df_time: pd.DataFrame) -> None:
    """
    수강 일자에 연도를 붙이고, 오늘 날짜와 겹치는 행을 강조해서 보여주는 함수.

    - "12월 xx일"  -> 2025년
    - 그 외(01~11월) -> 2026년
    - 오늘 날짜와 같은 날짜는 "★" 마커로 강조
    """
    # 일자별 수강 시간을 초로 변환 (df_time에 추가)
    df_time['일자별 수강 시간'] = df_time['일자별 수강 시간'].replace('', np.nan)
    df_time['일자별 수강 시간(초)'] = df_time['일자별 수강 시간'].apply(time_to_seconds)

    # 수강일자에 연도 추가
    df_time['수강 일자_원본'] = df_time['수강 일자'].copy()
    df_time['수강 일자_날짜객체'] = df_time['수강 일자'].apply(parse_korean_date)
    df_time['수강 일자_연도포함'] = df_time['수강 일자'].apply(format_date_with_year)

    # 오늘 날짜
    today = datetime.now().date()
    print(f"📅 오늘 날짜: {today.strftime('%Y년 %m월 %d일')}")

    # 오늘 날짜와 일치하는 행 확인
    df_time['오늘_일치'] = df_time['수강 일자_날짜객체'].apply(
        lambda x: x.date() == today if x is not None else False
    )

    # 오늘 날짜와 일치하는 행 개수
    today_count = df_time['오늘_일치'].sum()
    print(f"✅ 오늘 날짜와 일치하는 수강 기록: {today_count}개\n")

    # 수강일자별 클립 시간 재조회 (연도 포함)
    df_date_updated = df_time[df_time['수강 일자_날짜객체'].notna()].copy()

    if len(df_date_updated) > 0:
        # 수강 일자별로 클립 시간 합산 (연도 포함된 날짜로 그룹화)
        date_summary_updated = df_date_updated.groupby('수강 일자_연도포함').agg({
            '클립 시간(초)': 'sum',
            '일자별 수강 시간(초)': 'first',
            '클립명': 'count',
            '수강 일자_날짜객체': 'first',
            '오늘_일치': 'any'
        }).reset_index()

        date_summary_updated.columns = ['수강 일자', '클립 시간 합계(초)', '일자별 수강 시간(초)', '클립 개수', '날짜객체', '오늘_일치']
        date_summary_updated['클립 시간 합계'] = date_summary_updated['클립 시간 합계(초)'].apply(seconds_to_time)
        date_summary_updated['일자별 수강 시간'] = date_summary_updated['일자별 수강 시간(초)'].apply(seconds_to_time)

        # 날짜순으로 정렬
        date_summary_updated = date_summary_updated.sort_values('날짜객체')

        # 전체 합계
        total_clip_seconds = date_summary_updated['클립 시간 합계(초)'].sum()
        total_daily_seconds = date_summary_updated['일자별 수강 시간(초)'].sum()

        print("=" * 80)
        print("📅 수강 일자별 클립 시간 종합 정리 (연도 포함)")
        print("=" * 80)
        print(f"\n✅ 수강 일자가 기록된 데이터: {len(df_date_updated)}개")
        print(f"✅ 수강 일자 수: {len(date_summary_updated)}일")
        print(f"\n📊 전체 요약:")
        print(f"   - 클립 시간 총합: {seconds_to_time(int(total_clip_seconds))}")
        print(f"   - 일자별 수강 시간 총합: {seconds_to_time(int(total_daily_seconds))}")

        print(f"\n📅 일자별 상세 내역 (오늘 날짜는 ★로 표시):")
        print("-" * 80)

        # 표시할 컬럼만 선택
        display_df = date_summary_updated[['수강 일자', '클립 개수', '클립 시간 합계', '일자별 수강 시간', '오늘_일치']].copy()

        # 오늘 날짜 표시를 위해 마커 추가
        display_df['수강 일자'] = display_df.apply(
            lambda row: f"★ {row['수강 일자']}" if row['오늘_일치'] else row['수강 일자'],
            axis=1
        )

        # 오늘_일치 컬럼 제거하고 출력
        print_rich_table(
            display_df[['수강 일자', '클립 개수', '클립 시간 합계', '일자별 수강 시간']],
            title="연도 포함 수강 일자별 상세 내역 (★ = 오늘)"
        )

        # 오늘 날짜와 일치하는 행만 별도로 표시
        if today_count > 0:
            print(f"\n🎯 오늘 날짜({today.strftime('%Y년 %m월 %d일')}) 수강 기록:")
            print("-" * 80)
            today_records = date_summary_updated[date_summary_updated['오늘_일치']][
                ['수강 일자', '클립 개수', '클립 시간 합계', '일자별 수강 시간']
            ]
            print_rich_table(today_records, title="오늘 날짜 수강 기록")
    else:
        print("⚠️ 수강 일자가 기록된 데이터가 없습니다.")


def main() -> None:
    """
    메인 실행 함수.

    1) CSV 데이터 로드 및 기본 정보 출력
    2) 클립 시간 분석
    3) 수강 일자별 분석
    4) 연도 포함 수강 일자별 분석 + 오늘 날짜 강조
    5) README.md 생성
    """
    # 데이터 로드 (경로는 load_data 함수 내부에서 자동 설정)
    print("=" * 80)
    print("📂 데이터 로드")
    print("=" * 80)
    df = load_data()

    # 데이터 확인
    print(f"\n데이터 shape: {df.shape}")
    print(f"\n컬럼명:")
    print(df.columns.tolist())
    print(f"\n첫 5개 행:")
    print_rich_table(df.head(), title="원본 데이터 (상위 5행)")

    # 클립 시간 분석
    print("\n\n")
    df_time = analyze_clip_time(df)

    # 수강 일자별 분석
    print("\n\n")
    analyze_by_date(df_time)

    # 연도 포함 수강 일자별 분석
    print("\n\n")
    analyze_by_date_with_year(df_time)

    # README.md 생성
    print("\n\n")
    print("=" * 80)
    print("📝 README.md 생성")
    print("=" * 80)
    import subprocess
    import sys
    script_dir = Path(__file__).parent
    generate_readme_path = script_dir / 'generate_readme.py'
    if generate_readme_path.exists():
        subprocess.run([sys.executable, str(generate_readme_path)], check=True)
    else:
        print("⚠️ generate_readme.py를 찾을 수 없습니다.")


if __name__ == "__main__":
    main()
