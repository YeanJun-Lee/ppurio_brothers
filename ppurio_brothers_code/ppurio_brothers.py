import os
import requests
import json
import openai
import cv2
import easyocr
import numpy as np
from PIL import Image, ImageDraw, ImageFont


# 환경 변수에서 API KEY 가져오기
openai_api_key = os.getenv('OPENAI_API_KEY')
stability_api_key = os.getenv('STABLE_API_KEY')

# Open API Key 등록
client = openai.OpenAI(api_key = openai_api_key)

# 스타일 ID와 그림체 및 폰트 매핑
STYLE_MAP = {
    "style1": {
        "art_style": "a modern and professional style with clean, sleek design elements",
        "font": "/home/ec2-user/font/NotoSansKR-VariableFont_wght.ttf"
    },
    "style2": {
        "art_style": "a classic and elegant style featuring serif fonts and soft colors",
        "font": "/home/ec2-user/font/NanumMyeongjo-Regular.ttf"
    },
    "style3": {
        "art_style": "an eco-friendly style with earthy tones and natural elements",
        "font": "/home/ec2-user/font/Spoqa Han Sans Regular.ttf"        
    },
    "style4": {
        "art_style": "a warm and friendly local event style with cozy, inviting visuals",
        "font": "/home/ec2-user/font/BMHANNA_11yrs_ttf.ttf"
    },
    "style5": {
        "art_style": "a practical, information-focused style with clear, concise visuals",
        "font": "/home/ec2-user/font/NanumGothic-Regular.ttf"
    },
    "style6": {
        "art_style": "a viral social media style with bold, eye-catching visuals",
        "font": "/home/ec2-user/font/BMDOHYEON_ttf.ttf"
    }
}

# 키워드 추출 함수
def extract_keywords(user_input):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "You are an assistant that extracts event details for a poster. "
                        "Extract the following keys from the user input: "
                        "'목적', '일시', '장소', '주최', '이벤트명', '대상', '문의처'. "
                        "If a key is missing, leave its value empty. Reply in JSON format only."},
            {"role": "user", "content": user_input}
        ]
    )
    try:
        extracted_info = json.loads(response.choices[0].message.content)
        return extracted_info
    except json.JSONDecodeError:
        print("Error: Failed to parse GPT response.")
        return {key: "" for key in ["목적", "일시", "장소", "주최", "이벤트명", "대상", "문의처"]}

# GPT로 동적 우선순위 할당
def assign_priority(extracted_info):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "You are an assistant that assigns priorities to event keywords. "
                        "Based on the extracted keywords, assign a priority (1 to 7) to each key. "
                        "Smaller numbers indicate higher priority. Reply strictly in JSON format, e.g., "
                        "{'목적': 1, '일시': 2, '장소': 3, ...}"},
            {"role": "user", "content": f"Extracted keywords: {json.dumps(extracted_info)}"}
        ]
    )
    try:
        priorities = json.loads(response.choices[0].message.content)
        return priorities
    except json.JSONDecodeError:
        print("Error: Failed to parse GPT response for priorities.")
        return {key: 999 for key in extracted_info.keys()}  # 낮은 우선순위로 처리

# 우선순위에 따라 키워드 선택 (부족한 부분 채우기)
def select_keywords(user_selected_keywords, extracted_info, priority_order, max_keywords=3):
    """
    사용자 입력 키워드를 우선 반영하고, 부족한 키워드는 우선순위에 따라 자동으로 채운다.
    """
    # 사용자 입력 키워드 우선 반영
    selected_keywords = {}
    for key in user_selected_keywords:
        # 사용자 입력 키워드는 추출된 정보에 없더라도 추가
        selected_keywords[key] = extracted_info.get(key, "") if key in extracted_info else ""

    # 부족한 키워드 자동 채우기
    if len(selected_keywords) < max_keywords:
        remaining_keywords = {
            key: value for key, value in extracted_info.items()
            if key not in selected_keywords and value.strip()
        }
        # 우선순위 정렬 후 부족한 키워드 추가
        sorted_remaining = sorted(remaining_keywords.items(), key=lambda item: priority_order.get(item[0], 999))
        for key, value in sorted_remaining:
            if len(selected_keywords) < max_keywords:
                selected_keywords[key] = value

    return selected_keywords



# 스타일에 따른 그림체 선택
def get_art_style(style_id):
    return STYLE_MAP.get(style_id, {}).get("art_style", "a generic promotional poster style")

# 스타일에 따른 폰트 추천 (하나만 반환)
def recommend_font_by_style(style_id):
    return STYLE_MAP.get(style_id, {}).get("font", "Noto Sans KR")

# DALL·E로 포스터 생성
def generate_poster_with_dalle(prompt, art_style):
    full_prompt = f"{prompt}. Use {art_style}."
    response = client.images.generate(
        prompt=full_prompt,
        model="dall-e-3",
        n=1,
        size="1024x1024",
        quality="standard",
    )
    image_url = response.data[0].url
    print("포스터 생성 URL:", image_url)
    return image_url

# 이미지 저장 함수
def save_image_as_png(image_url, output_path):
    """
    이미지 URL에서 다운로드하여 PNG로 저장
    """
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Image saved to {output_path}")
    else:
        raise Exception(f"Failed to download image. Status code: {response.status_code}")

# JSON 데이터 저장 함수
def save_data_as_json(font, keywords, output_path):
    """
    추천 폰트와 키워드를 JSON 파일로 저장
    """
    data = {
        "recommended_font": font,
        "keywords": keywords
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"JSON data saved to {output_path}")

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

def extract_boxes_from_mask(mask_path):
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    _, thresh = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        boxes.append((x, y, w, h))
    
    # 큰 박스부터 정렬 (넓이 기준)
    boxes.sort(key=lambda b: b[2] * b[3], reverse=True)
    return boxes

def calculate_center_and_color(box, image_path):
    x, y, w, h = box
    center_x = x + w // 2
    center_y = y + h // 2

    # 이미지 로드 및 중심점의 색상 가져오기
    image = cv2.imread(image_path)
    b, g, r = image[center_y, center_x]  # BGR -> RGB
    return (center_x, center_y), (r, g, b)

def calculate_complementary_color(rgb_color):
    r, g, b = rgb_color
    return (255 - r, 255 - g, 255 - b)

def insert_text(draw, text, box, color, font_path, font_size):
    x, y, w, h = box
    center_x, center_y = x + w // 2, y + h // 2

    # 폰트 설정
    font = ImageFont.truetype(font_path, font_size)

    # 텍스트 크기 계산
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

    # 텍스트가 박스를 벗어나지 않도록 폰트 크기 조정
    while text_width > w or text_height > h:
        font_size -= 1  # 폰트 크기 줄이기
        font = ImageFont.truetype(font_path, font_size)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

    # 중앙 정렬
    text_position = (center_x - text_width // 2, center_y - text_height // 2)

    # 텍스트 삽입
    draw.text(text_position, text, fill=color, font=font)

def file_input(prompt_path):
    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read().replace('\n', ' ').strip() # 줄바꿈 및 앞 뒤 공백 제거
    

# 이미지 규격 줄이는 함수
def resize_existing_image(input_path, output_path):
    """
    기존 이미지를 불러와 MMS 규격(640x480)으로 줄입니다.
    PNG 형식으로 저장됩니다.
    :param input_path: 기존 이미지 경로 (final_path)
    :param output_path: 크기 조정된 이미지 저장 경로
    """
    mms_size = (640, 480)  # MMS 표준 크기
    with Image.open(input_path) as img:
        # 비율 유지하며 크기 조정
        img.thumbnail(mms_size, Image.Resampling.LANCZOS)
        img.save(output_path, format="PNG")  # PNG 형식으로 저장
        print(f"이미지가 MMS 규격으로 {output_path}에 저장되었습니다.")

# 실행 코드
def main():
    # 경로 설정
    OUTPUT_DIR = "/home/ec2-user/images"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 사용자 입력 Json으로 받기
    with open("/home/ec2-user/prompt/prompt.json", "r", encoding="utf-8") as file :
        prompt_data = json.load(file)
    
    # Json 데이터를 변수에 저장
    user_input = prompt_data.get("message", "") # 메세지를 입력받음
    brand_input = ""  # 브랜드 입력 없음
    selected_style = prompt_data.get("style", "")

    # 프론트엔드에서 입력받은 키워드 (사용자가 입력하지 않으면 빈 리스트)
    user_selected_keywords = prompt_data.get("keywords", [])[:3] # 최대 3개 이하
    user_selected_keywords = [kw.strip() for kw in user_selected_keywords if kw.strip()]

    # 키워드 추출
    extracted_info = extract_keywords(user_input)
    print("추출된 정보:", extracted_info)

    # 동적으로 우선순위 결정
    priority_order = assign_priority(extracted_info)
    print("동적으로 결정된 우선순위:", priority_order)

    # 사용자 선택 및 자동 선택 키워드 합성
    top_keywords = select_keywords(user_selected_keywords, extracted_info, priority_order)
    print("최종 선택된 키워드 (최대 3개):", top_keywords)

    # 포스터 생성 프롬프트
    keyword_text = ", ".join([f"{key}: {value}" for key, value in top_keywords.items()])
    dalle_prompt = f"A high-quality promotional poster with the following details prominently displayed: {keyword_text}. Align with {brand_input} branding."
    print("포스터 생성 프롬프트:", dalle_prompt)

    # 스타일에 따른 그림체 선택
    art_style = get_art_style(selected_style)
    print("선택된 그림체 스타일:", art_style)

    # 스타일에 따른 폰트 추천 (하나만)
    recommended_font = recommend_font_by_style(selected_style)
    print("추천된 폰트:", recommended_font)

    # 이미지 생성, 텍스트 제거, 키워드 삽입까지 반복
    for i in range(1, 4): 
        # 파일 경로 설정
        image_path = os.path.join(OUTPUT_DIR, f"origin_image/poster_{i}.png")
        mask_path = os.path.join(OUTPUT_DIR, f"mask/mask_{i}.png")
        output_path = os.path.join(OUTPUT_DIR, f"output/output_{i}.png")
        json_path = os.path.join(OUTPUT_DIR, f"origin_image/data_{i}.json")
        final_path = os.path.join(OUTPUT_DIR, f"final_output/final_poster_{i}.png")
        final_mms_path = os.path.join(OUTPUT_DIR, f"final_mms_output/final_mms_{i}.png")

        print(f"\n[PROCESSING IMAGE {i}]")
        # DALL·E로 포스터 생성
        poster_image_url = generate_poster_with_dalle(dalle_prompt, art_style)
        print(f"Image {i} 생성 URL:", poster_image_url)

        # 이미지 저장
        save_image_as_png(poster_image_url, image_path)
        print(f"Image {i} 저장 완료: {image_path}")

        # JSON 데이터 저장
        save_data_as_json(recommended_font, top_keywords, json_path)

        # 마스크 생성
        create_mask(image_path, mask_path)

        # Stability AI를 사용한 텍스트 제거
        erase(image_path, mask_path, output_path, stability_api_key)

        print(f"Image {i} 텍스트 제거 완료: {output_path}")

        # 텍스트 삽입
        # JSON 파일에서 키워드와 폰트 정보 가져오기
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 키워드 리스트 가져오기
        keywords = [
            value if value != "" else key
            for key, value in data["keywords"].items()
        ]

        # 박스와 키워드 매칭
        boxes = extract_boxes_from_mask(mask_path)
        image = Image.open(output_path)
        draw = ImageDraw.Draw(image)

        for box, keyword in zip(boxes, keywords):
            if not keyword:  # 키워드가 비어있으면 건너뜀
                continue

            font_size = int(min(box[2], box[3]) * 0.5)  # 박스 크기에 비례한 폰트 크기

            # 중심점과 중심 색상 계산
            center, original_color = calculate_center_and_color(box, output_path)
            complementary_color = calculate_complementary_color(original_color)

            # 텍스트 삽입
            insert_text(draw, keyword, box, complementary_color, recommended_font, font_size)
            print(f"Image {i}: '{keyword}' inserted into box {box}")

        # 결과 저장
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        image.save(final_path)
        print(f"Image {i} with keywords saved at {final_path}")

        # MMS 규격 맞춤
        resize_existing_image(final_path, final_mms_path)
        print(f"Image {i} MMS료 규격 수정 : {final_mms_path}")
        

    print("\n[ALL IMAGES PROCESSED AND KEYWORDS INSERTED]")

if __name__ == "__main__":
    main()