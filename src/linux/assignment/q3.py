# # 3번 2020년 충청북도 청주시 서원구 사고다발지역 검색하기(XML파일)

import requests
from urllib.parse import urlencode, unquote
from pathlib import Path

ENDPOINT = "http://apis.data.go.kr/B552061/frequentzoneLg/getRestFrequentzoneLg"


SERVICE_KEY_ENCODED = "08bc254bfb961e5e8fe573ab291525630c010c4abcd582a54e32c3e35d7f5c0c"
SERVICE_KEY = unquote(SERVICE_KEY_ENCODED)



# 3번 2020년 충청북도 청주시 서원구 사고다발지역 검색하기(XML파일)
def fetch_frequentzone(params: dict, fmt: str = "xml", timeout: int = 5):
    query = {
        "ServiceKey": SERVICE_KEY,
        "searchYearCd": params["year"],
        "siDo": params["sido"],
        "guGun": params["gugun"],
        "type": fmt,
        "numOfRows": 100,
        "pageNo": 1,
    }
    url = f"{ENDPOINT}?" + urlencode(query)
    print("요청 URL:", url)
    try:
        res = requests.get(url, timeout=timeout)
        res.raise_for_status()
    except requests.Timeout:
        print(f"타임아웃({timeout}s)")
        return None
    except requests.HTTPError as e:
        print("HTTPError:", e)
        print(res.text[:1000])
        return res
    return res

params_cb_cheongju_seowon_2020 = {"year": 2020, "sido": "43", "gugun": "112"}
res_cb_xml = fetch_frequentzone(params_cb_cheongju_seowon_2020, fmt="xml")
print("응답 상태 코드:", res_cb_xml.status_code)
if res_cb_xml.status_code == 200:
    print(res_cb_xml.text[:1000])
    out_path = Path("2020_cb_cheongju_seowon.xml")
    with out_path.open("w", encoding="utf-8") as f:
        f.write(res_cb_xml.text)
    print(f"저장 완료: {out_path}")
else:
    print(res_cb_xml.text)
