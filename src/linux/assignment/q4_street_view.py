import requests

service_key = '73e5010a0b1e94eb8f8be768621acc0c1b723a49675b563ac431ea8bc1143239'
url = 'https://apis.data.go.kr/B552061/frequentzoneLg/getRestFrequentzoneLg'

params = {
    'serviceKey': service_key,
    'searchYearCd': '2018',   
    'siDo': '11',             
    'guGun': '230',        
    'type': 'json',  # 가공하기 쉽게 json으로        
    'numOfRows': '10',
    'pageNo': '1'
}

try:
    res = requests.get(url, params=params)
    
    print(f"상태 코드: {res.status_code}")
   
    data = res.json() # 가공하기 쉽게 json으로 
    print(data)
    
except Exception as e:
    print(f"에러 발생: {e}")

items = data['items']['item']

for item in items:

    spot_nm = item['spot_nm']   # json으로 받은 사고지점
    occrrnc_cnt = item['occrrnc_cnt']
    lat = item['la_crd']        # 위도
    lon = item['lo_crd']        # 경도
    
    # 구글 스트리트 뷰
    street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"
    
    print(f"지점명: {spot_nm}")
    print(f"사고건수: {occrrnc_cnt}건")
    print(f"실제 도로 보기(로드뷰): {street_view_url}")