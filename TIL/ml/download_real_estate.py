"""
서울시 부동산 실거래가 정보 다운로드 스크립트
- 데이터 출처: 서울 열린데이터광장 (https://data.seoul.go.kr/dataList/OA-21275/S/1/datasetView.do)
- API 서비스명: tbLnOpendataRtmsV
- 기간: 2007년 1월 ~ 2023년 6월
"""

import os
import sys
import time
import json
import math
import requests
import pandas as pd
from pathlib import Path
from tqdm import tqdm


def load_env_file():
    """프로젝트 루트의 .env 파일에서 환경변수를 로드합니다."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


# .env 파일 로드
load_env_file()

# ──────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────
API_KEY = os.environ.get("SEOUL_API_KEY", "")  # .env 파일 또는 환경변수
SERVICE_NAME = "tbLnOpendataRtmsV"
BASE_URL = "http://openapi.seoul.go.kr:8088"
BATCH_SIZE = 1000  # 한 번에 요청할 행 수 (최대 1000)
SAVE_DIR = Path(__file__).parent / "data"

# 다운로드 연도 범위
START_YEAR = 2007
END_YEAR = 2023
END_MONTH = 6  # 2023년은 6월까지만


def fetch_data(api_key: str, start: int, end: int, acc_year: int) -> dict:
    """서울 열린데이터광장 API를 호출하여 데이터를 가져옵니다."""
    url = f"{BASE_URL}/{api_key}/json/{SERVICE_NAME}/{start}/{end}/{acc_year}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  [오류] API 요청 실패: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"  [오류] JSON 파싱 실패: {e}")
        return None


def get_total_count(api_key: str, acc_year: int) -> int:
    """해당 연도의 전체 데이터 건수를 조회합니다."""
    data = fetch_data(api_key, 1, 1, acc_year)
    if data and SERVICE_NAME in data:
        result = data[SERVICE_NAME].get("RESULT", {})
        code = result.get("CODE", "")
        if code == "INFO-000":
            return data[SERVICE_NAME].get("list_total_count", 0)
        elif code == "INFO-200":
            print(f"  [안내] {acc_year}년: 데이터가 없습니다.")
            return 0
        else:
            print(f"  [오류] {acc_year}년: {result.get('MESSAGE', '알 수 없는 오류')}")
            return 0
    return 0


def download_year_data(api_key: str, acc_year: int) -> pd.DataFrame:
    """특정 연도의 전체 데이터를 다운로드합니다."""
    total = get_total_count(api_key, acc_year)
    if total == 0:
        return pd.DataFrame()

    total_batches = math.ceil(total / BATCH_SIZE)
    all_rows = []
    start = 1
    retry_count = 0
    max_retries = 3

    pbar = tqdm(
        total=total,
        desc=f"  {acc_year}년",
        unit="건",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
    )

    while start <= total:
        end = min(start + BATCH_SIZE - 1, total)
        data = fetch_data(api_key, start, end, acc_year)

        if data and SERVICE_NAME in data:
            result = data[SERVICE_NAME].get("RESULT", {})
            if result.get("CODE") == "INFO-000":
                rows = data[SERVICE_NAME].get("row", [])
                all_rows.extend(rows)
                retry_count = 0
                pbar.update(len(rows))
            else:
                retry_count += 1
                if retry_count >= max_retries:
                    pbar.write(f"  [오류] 최대 재시도 횟수 초과 (start={start})")
                    break
                pbar.write(f"  [재시도 {retry_count}/{max_retries}] start={start}")
                time.sleep(2)
                continue
        else:
            retry_count += 1
            if retry_count >= max_retries:
                pbar.write(f"  [오류] 최대 재시도 횟수 초과 (start={start})")
                break
            pbar.write(f"  [재시도 {retry_count}/{max_retries}] start={start}")
            time.sleep(2)
            continue

        start = end + 1
        time.sleep(0.2)  # API 부하 방지

    pbar.close()

    if all_rows:
        return pd.DataFrame(all_rows)
    return pd.DataFrame()


def main():
    # API 키 확인
    api_key = API_KEY
    if not api_key:
        if len(sys.argv) > 1:
            api_key = sys.argv[1]
        else:
            api_key = input("서울 열린데이터광장 API 인증키를 입력하세요: ").strip()

    if not api_key:
        print("[오류] API 인증키가 필요합니다.")
        print("사용법: python download_real_estate.py <API_KEY>")
        print("또는 환경변수 SEOUL_API_KEY를 설정하세요.")
        sys.exit(1)

    # 저장 디렉토리 생성
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("서울시 부동산 실거래가 정보 다운로드")
    print(f"기간: {START_YEAR}년 ~ {END_YEAR}년 {END_MONTH}월")
    print(f"저장 경로: {SAVE_DIR}")
    print("=" * 60)

    all_data = []
    years = range(START_YEAR, END_YEAR + 1)

    for year in tqdm(years, desc="전체 진행", unit="년"):
        year_file = SAVE_DIR / f"seoul_real_estate_{year}.csv"

        # 이어받기: 이미 다운로드된 연도는 건너뛰기
        if year_file.exists():
            existing_df = pd.read_csv(year_file, encoding="utf-8-sig")
            all_data.append(existing_df)
            tqdm.write(f"[{year}년] 이미 다운로드됨 ({len(existing_df):,}건), 건너뜀")
            continue

        tqdm.write(f"[{year}년] 데이터 다운로드 중...")
        df = download_year_data(api_key, year)

        if df.empty:
            tqdm.write(f"  {year}년: 데이터 없음, 건너뜀")
            continue

        # 2023년은 6월까지만 필터링
        if year == END_YEAR:
            if "CTRT_DAY" in df.columns:
                # CTRT_DAY는 YYYYMMDD 형식
                df["CTRT_DAY"] = df["CTRT_DAY"].astype(str)
                df = df[df["CTRT_DAY"].str[:6] <= f"{END_YEAR}{END_MONTH:02d}"]
                tqdm.write(f"  {year}년 {END_MONTH}월까지 필터링 후: {len(df):,}건")

        all_data.append(df)
        tqdm.write(f"  {year}년: {len(df):,}건 완료")

        # 연도별 CSV 저장 (개별 파일)
        df.to_csv(year_file, index=False, encoding="utf-8-sig")
        tqdm.write(f"  저장: {year_file.name}")

    # 전체 데이터 병합 및 저장
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        combined_file = SAVE_DIR / "seoul_real_estate_2007_2023.csv"
        combined.to_csv(combined_file, index=False, encoding="utf-8-sig")
        print("\n" + "=" * 60)
        print(f"전체 데이터: {len(combined):,}건")
        print(f"통합 파일 저장: {combined_file}")
        print(f"연도별 파일 저장: {SAVE_DIR}/seoul_real_estate_YYYY.csv")
        print("=" * 60)
    else:
        print("\n[경고] 다운로드된 데이터가 없습니다.")


if __name__ == "__main__":
    main()
