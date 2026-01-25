import requests
from pathlib import Path

serviceKey = '7d61e376c696ad016487e4d7171f2fc54a968f6031076d0ee40cbf4747a3b2e1'

# 2021년 서울특별시 중랑구 사고다발지역 이미지 (가로 1024 x 세로 1024) 조회
url = 'http://apis.data.go.kr/B552061/frequentzoneLg/getWMSFrequentzoneLg?'
layers = 'frelg'
format = 'image/png'
transparent = 'true'
service = 'WMS'
version = '1.1.1'
request = 'GetMap'
srs = 'EPSG:4326'
bbox = '126.966,37.484,127.103,37.623'
width = '1024'
height = '1024'
searchYearCd = '2021'
siDo = '11'
guGun = '260'
params = {
    'ServiceKey': serviceKey,
    'searchYearCd': searchYearCd,
    'siDo': siDo,
    'guGun': guGun,
    'layers': layers,
    'format': format,
    'transparent': transparent,
    'service': service,
    'version': version,
    'request': request,
    'srs': srs,
    'bbox': bbox,
    'width': width,
    'height': height,
}

response = requests.get(url, params=params, stream=True)

# 응답 상태 코드 출력
print("status_code:", response.status_code)

if response.status_code != 200:
    print("요청 실패:", response.text)
    raise SystemExit

# 이 스크립트(q5.py)가 있는 디렉터리 기준으로 asset 폴더 생성
base_dir = Path(__file__).resolve().parent
asset_dir = base_dir / "asset"
asset_dir.mkdir(parents=True, exist_ok=True)

# 이미지 파일을 asset 폴더에 저장
output_path = asset_dir / "2021_seoul_jungnang_from_api2.png"
with open(output_path, 'wb') as f:
    f.write(response.content)

print("이미지 저장 완료:", output_path)
