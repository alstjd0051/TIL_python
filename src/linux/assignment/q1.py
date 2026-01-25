import requests

url = "https://apis.data.go.kr/B552061/frequentzoneLg/getRestFrequentzoneLg"

params = {
    "ServiceKey": "848657a69b91ed1e08a3e7f20866818f1e75fc51d3c2446a988d10da041f20f1",
    "searchYearCd": "2019",
    "siDo": "제주특별자치도",
    "guGun": "서귀포시",
    "numOfRows": "100",
    "pageNo": "1",
    "type": "xml"
}

response = requests.get(url, params=params, timeout=10)

print("요청 URL:", response.url)
print("상태코드:", response.status_code)
print(response.text)
