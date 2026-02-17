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

from rich.console import Console
from rich.table import Table

from freeboards.utils import (
    time_to_seconds,
    seconds_to_time,
    parse_korean_date,
    format_date_with_year,
    load_data,
    get_today,
)

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

    for col in df.columns:
        table.add_column(str(col))

    for _, row in df.head(max_rows).iterrows():
        table.add_row(*[str(v) for v in row.values])

    console.print(table)


def analyze_clip_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    클립 시간 관련 통계를 계산하고 출력하는 함수.

    - 전체 클립 개수 / 총 시간 / 평균 시간
    - 강의별 클립 시간 요약
    - 파트별 클립 시간 요약
    """
    df_time = df.copy()
    df_time['클립 시간'] = df_time['클립 시간'].replace('', np.nan)
    df_time['클립 시간(초)'] = df_time['클립 시간'].apply(time_to_seconds)

    total_seconds = df_time['클립 시간(초)'].sum()
    total_time_str = seconds_to_time(total_seconds)

    print("=" * 60)
    print("📊 클립 시간 종합 분석")
    print("=" * 60)
    print(f"\n✅ 전체 클립 개수: {len(df_time)}개")
    print(f"✅ 클립 시간이 있는 데이터: {df_time['클립 시간(초)'].notna().sum()}개")
    print(f"✅ 총 클립 시간: {total_time_str} ({total_seconds:,}초)")
    print(f"✅ 평균 클립 시간: {seconds_to_time(int(df_time['클립 시간(초)'].mean()))}")

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
    df_date = df_time[df_time['수강 일자'] != ''].copy()

    if len(df_date) > 0:
        df_date['일자별 수강 시간(초)'] = df_date['일자별 수강 시간'].apply(time_to_seconds)

        date_summary_with_daily = df_date.groupby('수강 일자').agg({
            '클립 시간(초)': 'sum',
            '일자별 수강 시간(초)': 'first',
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

        total_clip_seconds = date_summary_with_daily['클립 시간 합계(초)'].sum()
        total_daily_seconds = date_summary_with_daily['일자별 수강 시간(초)'].sum()

        print(f"\n📊 전체 요약:")
        print(f"   - 클립 시간 총합: {seconds_to_time(int(total_clip_seconds))}")
        print(f"   - 일자별 수강 시간 총합: {seconds_to_time(int(total_daily_seconds))}")

        print(f"\n📅 일자별 상세 내역:")
        print("-" * 80)
        detail_df = date_summary_with_daily[['수강 일자', '클립 개수', '클립 시간 합계', '일자별 수강 시간']].sort_values('수강 일자')
        print_rich_table(detail_df, title="수강 일자별 상세 내역")

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

    - 연도는 현재 날짜 기준으로 자동 계산
    - 오늘 날짜와 같은 날짜는 "★" 마커로 강조
    """
    df_time['일자별 수강 시간'] = df_time['일자별 수강 시간'].replace('', np.nan)
    df_time['일자별 수강 시간(초)'] = df_time['일자별 수강 시간'].apply(time_to_seconds)

    df_time['수강 일자_원본'] = df_time['수강 일자'].copy()
    df_time['수강 일자_날짜객체'] = df_time['수강 일자'].apply(parse_korean_date)
    df_time['수강 일자_연도포함'] = df_time['수강 일자'].apply(format_date_with_year)

    today = get_today()
    print(f"📅 오늘 날짜: {today.strftime('%Y년 %m월 %d일')}")

    df_time['오늘_일치'] = df_time['수강 일자_날짜객체'].apply(
        lambda x: x.date() == today if x is not None else False
    )

    today_count = df_time['오늘_일치'].sum()
    print(f"✅ 오늘 날짜와 일치하는 수강 기록: {today_count}개\n")

    df_date_updated = df_time[df_time['수강 일자_날짜객체'].notna()].copy()

    if len(df_date_updated) > 0:
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

        date_summary_updated = date_summary_updated.sort_values('날짜객체')

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

        display_df = date_summary_updated[['수강 일자', '클립 개수', '클립 시간 합계', '일자별 수강 시간', '오늘_일치']].copy()

        display_df['수강 일자'] = display_df.apply(
            lambda row: f"★ {row['수강 일자']}" if row['오늘_일치'] else row['수강 일자'],
            axis=1
        )

        print_rich_table(
            display_df[['수강 일자', '클립 개수', '클립 시간 합계', '일자별 수강 시간']],
            title="연도 포함 수강 일자별 상세 내역 (★ = 오늘)"
        )

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
    print("=" * 80)
    print("📂 데이터 로드")
    print("=" * 80)
    df = load_data()

    print(f"\n데이터 shape: {df.shape}")
    print(f"\n컬럼명:")
    print(df.columns.tolist())
    print(f"\n첫 5개 행:")
    print_rich_table(df.head(), title="원본 데이터 (상위 5행)")

    print("\n\n")
    df_time = analyze_clip_time(df)

    print("\n\n")
    analyze_by_date(df_time)

    print("\n\n")
    analyze_by_date_with_year(df_time)

    print("\n\n")
    print("=" * 80)
    print("📝 README.md 생성")
    print("=" * 80)
    from freeboards.generate_readme import main as generate_readme
    generate_readme()


if __name__ == "__main__":
    main()
