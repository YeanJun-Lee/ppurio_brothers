import openai
import cv2
import easyocr
import numpy as np
import os
import matplotlib.pyplot as plt
import requests
from PIL import Image
from io import BytesIO

# 환경 변수에서 API KEY 가져오기
openai_api_key = os.getenv('OPENAI_API_KEY')
stability_api_key = os.getenv('STABLE_API_KEY')

# Open API Key 등록
client = openai.OpenAI(api_key = openai_api_key)

# prompt 기반 이미지 생성 함수
# prompt 와 save_path를 매개변수로 받아 이미지를 생성한다. 
def generate_image(prompt_file_path, save_path):

    # prompt.txt 파일에서 prompt 읽기
    with open(prompt_file_path, 'r', encoding='utf-8') as file:
        prompt = file.read().strip() # 파일의 내용을 prompt로 사용

    # 이미지 생성 모듈
    response = client.images.generate(
        prompt = prompt,
        model="dall-e-3",
        n=1,
        size="1024x1024",
        quality="standard",
    )

    # 이미지를 URL을 통해 다운로드
    image_url = response.data[0].url
    image_data = requests.get(image_url).content

    # 이미지를 파일로 저장
    image = Image.open(BytesIO(image_data))
    image.save(save_path)

    # 성공적으로 저장한 경로를 반환한다.
    print(f"Generated Image saved at: {save_path}")
    return save_path

# EasyOCR을 활용한 이미지 mask 함수
def create_mask(image_path, mask_path):
    # OCR 객체 생성
    reader = easyocr.Reader(['en', 'ko'])

    # 이미지 불러오기
    origin_image = cv2.imread(image_path)

    # EasyOCR을 사용하여 텍스트 감지
    results = reader.readtext(image_path)

    # 텍스트 영역을 마킹하기 위한 흰색 이미지 생성 (원본 이미지와 동일한 크기)
    masked_image = np.zeros_like(origin_image)  # 초기화된 검정색 이미지 생성

    # 감지된 텍스트 영역을 흰색으로 마킹 
    for (bbox, text, prob) in results:
        # 박스 좌표 추출
        (top_left, top_right, bottom_right, bottom_left) = bbox
        top_left = tuple(map(int, top_left))
        bottom_right = tuple(map(int, bottom_right))

        # 텍스트 영역을 흰색으로 마킹 (255, 255, 255는 흰색)
        cv2.rectangle(masked_image, top_left, bottom_right, (255, 255, 255), -1)  # -1은 내부 채우기 옵션

    # 마킹된 이미지를 파일로 저장 (검정색 배경에 흰색 텍스트 영역)
    masked_image_path = mask_path
    cv2.imwrite(masked_image_path, masked_image)

    # 성공적으로 저장한 경로를 반환한다.
    print(f"Making image mask saved at {mask_path}")
    return masked_image_path

# Stability API를 사용한 Erase 함수
def erase(image_path, mask_path, output_path, stability_api_key):
    # Stability API 엔트포인트 설정 (erase 기능)
    url = "https://api.stability.ai/v2beta/stable-image/edit/erase"

    # API 요청 설정
    headers = {
        "authorization": f"Bearer {stability_api_key}",
        "accept": "image/*"
    }

    # 이미지와 마스크 파일 업로드
    files = {
        "image": open(image_path, "rb"),
        "mask": open(mask_path, "rb")
    }

    # 데이터 설정
    data = {
        "output_format": "png", # 출력 이미지 포맷
    }

    # API 요청 보내기
    response = requests.post(url, headers=headers, files=files, data=data)

    # 응답 확인 및 처리
    if response.status_code == 200:
        # 텍스트가 제거된 이미지를 저장
        with open(output_path, "wb") as file:
            file.write(response.content)
        print(f"Erase text Sucessfully save as {output_path}")
    else :
        # 오류 발생 시 예외 처리
        raise Exception(f"Error: {response.status_code}, {response.json()}")

# 전체 흐름 실행
def main():
    
    prompt_file_path = "/home/ec2-user/prompt/prompt.txt"
    image_path = "/home/ec2-user/images/origin_image/image.png"
    mask_path = "/home/ec2-user/images/mask/mask.png"
    output_path = "/home/ec2-user/images/output/output.png"

    generate_image(prompt_file_path, image_path)
    create_mask(image_path, mask_path)
    erase(image_path, mask_path, output_path, stability_api_key)

    print(f"Image Process Complete")

if __name__ == "__main__":
    main()