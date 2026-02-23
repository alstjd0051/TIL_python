"""
README.md 생성 스크립트

freeboards 프로젝트 실행 시 README.md에 일자 스케줄을 출력합니다.
- 진도율 프로그레스 바
- 월별 접기(collapse) 상세 내역
- ✅ = 오늘 날짜 표시
"""

import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

from freeboards.utils import (
    time_to_seconds,
    seconds_to_time,
    parse_korean_date,
    format_date_with_year,
    load_data,
    get_today,
)


def _build_progress_bar(current: int, total: int, width: int = 20) -> str:
    """
    텍스트 기반 프로그레스 바를 생성하는 함수.

    예: [████████████░░░░░░░░] 60.0%
    """
    if total == 0:
        return "[░" * width + "] 0.0%"
    ratio = min(current / total, 1.0)
    filled = int(width * ratio)
    empty = width - filled
    percent = ratio * 100
    return f"[{'█' * filled}{'░' * empty}] {percent:.1f}%"


def generate_readme_markdown() -> str:
    """
    README.md 마크다운 내용을 생성하는 함수.

    Returns:
        str: README.md 마크다운 내용
    """
    df = load_data()

    df['클립 시간'] = df['클립 시간'].replace('', np.nan)
    df['클립 시간(초)'] = df['클립 시간'].apply(time_to_seconds)

    df['일자별 수강 시간'] = df['일자별 수강 시간'].replace('', np.nan)
    df['일자별 수강 시간(초)'] = df['일자별 수강 시간'].apply(time_to_seconds)

    df['수강 일자_날짜객체'] = df['수강 일자'].apply(parse_korean_date)
    df['수강 일자_연도포함'] = df['수강 일자'].apply(format_date_with_year)

    today = get_today()

    df['오늘_일치'] = df['수강 일자_날짜객체'].apply(
        lambda x: x.date() == today if x is not None else False
    )

    df_date_updated = df[df['수강 일자_날짜객체'].notna()].copy()

    if len(df_date_updated) == 0:
        return "# 수강 일정\n\n⚠️ 수강 일자가 기록된 데이터가 없습니다.\n"

    def unique_join(series):
        """고유한 값들을 콤마로 구분해서 반환"""
        unique_values = series.dropna().unique()
        unique_values = [str(v).strip() for v in unique_values if str(v).strip() != '']
        return ', '.join(unique_values) if unique_values else ''

    date_summary = df_date_updated.groupby('수강 일자_연도포함').agg({
        '클립 시간(초)': 'sum',
        '일자별 수강 시간(초)': 'first',
        '수강 일자_날짜객체': 'first',
        '파트명': unique_join,
        '클립명': unique_join
    }).reset_index()

    date_summary.columns = ['수강 일자', '클립 시간 합계(초)', '일자별 수강 시간(초)', '날짜객체', '파트명', '클립명']
    date_summary['클립 시간 합계'] = date_summary['클립 시간 합계(초)'].apply(seconds_to_time)
    date_summary['일자별 수강 시간'] = date_summary['일자별 수강 시간(초)'].apply(seconds_to_time)

    date_summary['오늘_일치'] = date_summary['날짜객체'].apply(
        lambda x: x.date() == today if x is not None else False
    )

    date_summary = date_summary.sort_values('날짜객체')

    # 전체 통계
    total_days = len(date_summary)
    total_clip_seconds = int(date_summary['클립 시간 합계(초)'].sum())
    total_daily_seconds = int(date_summary['일자별 수강 시간(초)'].sum())

    # 오늘 기준 진도율 계산 (캘린더 날짜 기준)
    first_date = date_summary['날짜객체'].min().date()
    last_date = date_summary['날짜객체'].max().date()
    total_calendar_days = (last_date - first_date).days + 1
    elapsed_calendar_days = min((today - first_date).days + 1, total_calendar_days)
    elapsed_calendar_days = max(elapsed_calendar_days, 0)
    progress_bar = _build_progress_bar(elapsed_calendar_days, total_calendar_days)

    # 월별 그룹 생성
    monthly_groups = defaultdict(list)
    for _, row in date_summary.iterrows():
        date_obj = row['날짜객체']
        month_key = f"{date_obj.year}년 {date_obj.month:02d}월"
        monthly_groups[month_key].append(row)

    # 마크다운 생성 시작
    lines = [
        "# 수강 일정",
        "",
        f"**업데이트 날짜**: {today.strftime('%Y년 %m월 %d일')}",
        "",
        "## 전체 요약",
        "",
        f"| 항목 | 값 |",
        f"|---|---|",
        f"| 수강 일자 수 | **{total_days}일** |",
        f"| 클립 시간 총합 | {seconds_to_time(total_clip_seconds)} |",
        f"| 일자별 수강 시간 총합 | {seconds_to_time(total_daily_seconds)} |",
        "",
        "## 진도율",
        "",
        f"```",
        f"{progress_bar} ({elapsed_calendar_days}/{total_calendar_days}일)",
        f"```",
        "",
        "## 월별 수강 내역",
        "",
    ]

    # 월별 접기(collapse) 섹션 생성
    for month_key, rows in monthly_groups.items():
        month_daily_seconds = sum(int(r['일자별 수강 시간(초)']) for r in rows)
        month_days = len(rows)

        # 현재 월인지 확인
        is_current_month = any(
            r['날짜객체'].year == today.year and r['날짜객체'].month == today.month
            for r in rows
        )
        marker = " (현재)" if is_current_month else ""

        lines.append(f"<details{'  open' if is_current_month else ''}>")
        lines.append(f"<summary><b>{month_key}{marker}</b> - {month_days}일, 수강 시간: {seconds_to_time(month_daily_seconds)}</summary>")
        lines.append("")
        lines.append("| 수강 일자 | 파트명 | 클립명 | 일자별 수강 시간 |")
        lines.append("|-----------|--------|--------|----------------|")

        for row in rows:
            date_str = row['수강 일자']
            if bool(row['오늘_일치']):
                date_str = f"✅ {date_str}"

            part_name = str(row['파트명']) if pd.notna(row['파트명']) else ''
            clip_name = str(row['클립명']) if pd.notna(row['클립명']) else ''

            part_name = part_name.replace('\n', ' ').replace('|', '\\|')
            clip_name = clip_name.replace('\n', ' ').replace('|', '\\|')

            lines.append(f"| {date_str} | {part_name} | {clip_name} | {row['일자별 수강 시간']} |")

        lines.append("")
        lines.append("</details>")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """
    메인 실행 함수.
    README.md 파일을 생성합니다.
    """
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    readme_path = project_root / 'README.md'

    markdown_content = generate_readme_markdown()

    readme_path.write_text(markdown_content, encoding='utf-8')
    print(f"✅ README.md가 생성되었습니다: {readme_path}")


if __name__ == "__main__":
    main()
