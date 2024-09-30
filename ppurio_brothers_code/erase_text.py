import requests

# Stability API key (실제 키로 교체)
API_KEY = "MyAPIKey"

# Stability API 엔드포인트 설정 (erase 기능)
url = "https://api.stability.ai/v2beta/stable-image/edit/erase"

# API 요청 설정
headers = {
    "authorization": f"Bearer {API_KEY}",
    "accept": "image/*"
}

# 이미지와 마스크 파일 업로드
files = {
    "image": open("ppurio_brothers_backup/image/origin_image/Image_test2.png", "rb"),  # 텍스트가 포함된 원본 이미지
    "mask": open("ppurio_brothers_backup/image/origin_image/Image_test2.png", "rb")  # 자동 감지된 텍스트 부분을 마스크로 만들어 제공
}

# 데이터 설정
data = {
    "output_format": "webp",  # 출력 이미지 포맷
}

# API 요청 보내기
response = requests.post(url, headers=headers, files=files, data=data)

# 응답 확인 및 처리
if response.status_code == 200:
    # 텍스트가 제거된 이미지를 저장
    with open("ppurio_brothers_backup/image/output/image_test2_output.png", 'wb') as file:
        file.write(response.content)
    print("텍스트가 제거된 이미지가 성공적으로 저장되었습니다.")
else:
    # 오류 발생 시 예외 처리
    raise Exception(f"Error: {response.status_code}, {response.json()}")