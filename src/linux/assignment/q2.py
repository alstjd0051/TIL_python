import requests
import json

url = "http://apis.data.go.kr/B552061/frequentzoneLg/getRestFrequentzoneLg"
params = {
    "ServiceKey": "c386fa19f5ffc8fd2ba488e31eb8faf60ad4cff30335e720fb0e4b12db95f614",
    "searchYearCd": "2017",
    "siDo": "41",
    "guGun": "390",
    "numOfRows": "100",
    "pageNo": "1",
    "type": "json",
}

response = requests.get(url, params=params)

# 상태 코드 확인 (200이 아니면 에러 출력 후 종료)
if response.status_code != 200:
    print("요청 실패:", response.status_code)
    print(response.text)
    raise SystemExit

# JSON 파싱
sh_list = response.json()

# items -> item 리스트 가져오기
items = sh_list["items"]["item"]

# 전체 항목 개수
n = len(items)
print("전체 항목 수:", n)

# spot_nm 만 뽑아서 리스트 만들기
spot_list = []
for i in range(n):
    temp = items[i]["spot_nm"]
    spot_list.append(temp)

print("spot_list:", spot_list)