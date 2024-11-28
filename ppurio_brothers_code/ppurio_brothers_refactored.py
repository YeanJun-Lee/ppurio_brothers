import os
import requests
import json
import openai
import cv2
import easyocr
import numpy as np
from multiprocessing import Pool
from io import BytesIO, StringIO
from PIL import Image, ImageDraw, ImageFont

# 환경 변ㅜ에서 API KEY 가져오기
openai_api_key = os.getenv('MyAPIKey')
stability_api_key = os.getenv('STABLE_API_KEY')

# Open API Key 등록
client = openai.OpenAI(api_key=openai_api_key)

# 스타일 ID와 그림체 및 폰트 매핑
STYLE_MAP = {
    "style1": {
        "art_style": "a modern and professional style with clean, sleek design elements",
        "font": "/home/ec2-user/font/NotoSansKR-Black.ttf"
    },
    "style2": {
        "art_style": "a classic and elegant style featuring serif fonts and soft colors",
        "font": "/home/ec2-user/font/NanumMyeongjo-ExtraBold.ttf"
    },
    "style3": {
        "art_style": "an eco-friendly style with earthy tones and natural elements",
        "font": "/home/ec2-user/font/Spoqa Han Sans Bold.ttf"        
    }, 
    "style4": {
        "art_style": "a warm and friendly local event style with cozy, inviting visuals",
        "font": "/home/ec2-user/font/BMHANNA_11yrs_ttf.ttf"
    },
    "style5": {
        "art_style": "a practical, information-focused style with clear, concise visuals",
        "font": "/home/ec2-user/font/NanumGothic-ExtraBold.ttf"
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
    return STYLE_MAP.get(style_id, {}).get("font", "/home/ec2-user/font/NotoSansKR-Black.ttf")

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

# 이미지 데이터를 요청하고 메모리로 로드
def load_image_data(image_url):
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        image_data = Image.open(response.raw) # 이미지를 버퍼로 저장
        print("Image loaded into buffer")
        return image_data
    else:
        raise Exception(f"Failed to download image. Status code: {response.status_code}")

# JSON 데이터 저장 함수 (버퍼 버전)
def save_data_as_json_buffer(font, keywords):
    """
    추천 폰트와 키워드를 JSON 형식으로 메모리에 저장
    """
    data = {
        "recommended_font": font,
        "keywords": keywords
    }
    # 메모리 버퍼에 JSON 데이터 저장
    buffer = StringIO()
    json.dump(data, buffer, ensure_ascii=False, indent=4)
    buffer.seek(0)
    print("JSON data saved to buffer")
    return buffer

# EasyOCR을 활용한 이미지 mask 함수 (image_data 사용 버전)
def create_mask_from_image_data(image_data):
    """
    PIL 이미지 객체를 입력받아 EasyOCR을 통해 텍스트 영역을 감지하고,
    해당 영역을 흰색으로 마킹한 이미지를 버퍼로 반환.
    """
    # OCR 객체 생성
    reader = easyocr.Reader(['en', 'ko'])

    # PIL 이미지를 OpenCV 형식으로 변환
    image_np = np.array(image_data)
    origin_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    # EasyOCR을 사용하여 텍스트 감지
    results = reader.readtext(origin_image)

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

    # 마킹된 이미지를 버퍼에 저장
    success, buffer = cv2.imencode('.png', masked_image)
    if success:
        print("Mask image saved to buffer")
        return BytesIO(buffer.tobytes())
    else:
        raise Exception("Failed to encode the image to buffer.")


# Stability API를 사용한 Erase 함수 (버퍼 버전)
def erase_to_buffer(image_data, mask_buffer, stability_api_key):
    """
    Stability API를 사용하여 이미지를 수정하고 결과 이미지를 버퍼로 반환.
    """
    # Stability API 엔드포인트 설정
    url = "https://api.stability.ai/v2beta/stable-image/edit/erase"

    # API 요청 설정
    headers = {
        "authorization": f"Bearer {stability_api_key}",
        "accept": "image/*"
    }

    # 이미지 데이터를 바이너리로 변환
    image_buffer = BytesIO()
    image_data.save(image_buffer, format="PNG")
    image_buffer.seek(0)  # 버퍼 시작 위치로 이동

    # Stability API에 업로드할 파일 준비
    files = {
        "image": ("image.png", image_buffer, "image/png"),
        "mask": ("mask.png", mask_buffer, "image/png")
    }

    # API 요청 데이터 설정
    data = {
        "output_format": "png"  # 출력 이미지 포맷
    }

    # API 요청 보내기
    response = requests.post(url, headers=headers, files=files, data=data)

    # 응답 확인 및 처리
    if response.status_code == 200:
        print("Text successfully erased from the image.")
        return BytesIO(response.content)  # 결과 이미지를 버퍼로 반환
    else:
        # 오류 발생 시 예외 처리
        error_message = response.json()
        raise Exception(f"Error: {response.status_code}, {error_message}")

# mask를 기반으로 큰 박스부터 정렬 
def extract_boxes_from_mask_buffer(mask_buffer):
    """
    마스크 이미지 버퍼를 사용하여 텍스트 영역의 경계 상자를 추출.
    """
    # 버퍼에서 이미지를 읽어 OpenCV 형식으로 변환
    mask_buffer.seek(0)  # 버퍼의 시작 위치로 이동
    mask_array = np.frombuffer(mask_buffer.read(), np.uint8)
    mask = cv2.imdecode(mask_array, cv2.IMREAD_GRAYSCALE)

    # 이진화 처리
    _, thresh = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)

    # 외곽선 감지
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 감지된 외곽선으로 경계 상자 생성
    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        boxes.append((x, y, w, h))

    # 큰 박스부터 정렬 (넓이 기준)
    boxes.sort(key=lambda b: b[2] * b[3], reverse=True)
    return boxes

# mask의 중심점의 색 도출
def calculate_center_and_color_from_buffer(box, image_buffer):
    """
    경계 상자와 이미지 버퍼를 사용하여 중심 좌표와 중심점의 색상을 계산.
    """
    x, y, w, h = box
    center_x = x + w // 2
    center_y = y + h // 2

    # 버퍼에서 이미지를 읽어 OpenCV 형식으로 변환
    image_buffer.seek(0)  # 버퍼의 시작 위치로 이동
    image_array = np.frombuffer(image_buffer.read(), np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    # 중심점의 색상 추출 (BGR -> RGB로 변환)
    b, g, r = image[center_y, center_x]
    return (center_x, center_y), (r, g, b)

# 보색 처리 
def calculate_complementary_color(rgb_color):
    r, g, b = rgb_color
    return (255 - r, 255 - g, 255 - b)

def insert_text_to_buffer(image_buffer, text, box, color, font_path, font_size):
    """
    이미지 버퍼에 텍스트를 삽입하고 수정된 이미지를 새로운 버퍼로 반환.
    """
    # 버퍼에서 이미지를 로드 (PIL 형식)
    image_buffer.seek(0)  # 버퍼의 시작 위치로 이동
    image = Image.open(image_buffer)

    # 텍스트 삽입을 위한 Draw 객체 생성
    draw = ImageDraw.Draw(image)

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

    # 수정된 이미지를 새로운 버퍼로 저장
    output_buffer = BytesIO()
    image.save(output_buffer, format="PNG")
    output_buffer.seek(0)  # 버퍼의 시작 위치로 이동
    print("Text inserted into image buffer")
    return output_buffer

# 사용자 입력 prompt JSON 파일 엔터 제거 
def file_input(prompt_path):
    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read().replace('\n', ' ').strip() # 줄바꿈 및 앞 뒤 공백 제거

# 이미지 생성 코드
def process_single_image(args):
    i, dalle_prompt, art_style, stability_api_key, json_buffer, recommended_font = args

    print(f"[PROCESSING IMAGE {i}]")

    # 각 이미지 생성 및 처리 코드
    poster_image_url = generate_poster_with_dalle(dalle_prompt, art_style)
    poster_image_data = load_image_data(poster_image_url)
    mask_buffer = create_mask_from_image_data(poster_image_data)
    erased_buffer = erase_to_buffer(poster_image_data, mask_buffer, stability_api_key)

    # JSON 데이터를 읽어 키워드 리스트 가져오기
    json_buffer.seek(0)
    data = json.load(json_buffer)
    keywords = [
        value if value != "" else key
        for key, value in data["keywords"].items()
    ]

    # 마스크에서 박스 추출
    boxes = extract_boxes_from_mask_buffer(mask_buffer)

    # 텍스트 삽입
    final_image_buffer = erased_buffer
    for box, keyword in zip(boxes, keywords):
        if not keyword:
            continue
        font_size = int(min(box[2], box[3]) * 0.5)  # 박스 크기에 비례한 폰트 크기
        center, original_color = calculate_center_and_color_from_buffer(box, final_image_buffer)
        complementary_color = calculate_complementary_color(original_color)
        final_image_buffer = insert_text_to_buffer(
            final_image_buffer, keyword, box, complementary_color, recommended_font, font_size
        )

    # BytesIO -> PIL.Image 변환 후 저장
    final_image_buffer.seek(0)
    final_image = Image.open(final_image_buffer)
    final_output_path = f"/home/ec2-user/images/final_output/final_poster_{i}.png"
    os.makedirs(os.path.dirname(final_output_path), exist_ok=True)
    final_image.save(final_output_path, format="PNG")
    print(f"Image {i} processing complete.\n")

# 실행 코드 
def main():
    # 사용자 입력 Json으로 받기
    with open("/home/ec2-user/prompt/prompt.json", "r", encoding="utf-8") as file:
        prompt_data = json.load(file)
    
    # Json 데이터를 변수에 저장
    user_input = prompt_data.get("message", "").replace("\n", " ") # 줄바꿈 제거
    brand_input = prompt_data.get("brand", "")
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

    # JSON 데이터 생성
    json_buffer = save_data_as_json_buffer(recommended_font, top_keywords)

    # 병렬 작업 설정
    num_images = 3
    args = [
        (i, dalle_prompt, art_style, stability_api_key, json_buffer, recommended_font)
        for i in range(1, num_images + 1)  # 3개의 이미지를 처리
    ]

    # 멀티프로세싱으로 병렬 처리
    with Pool(processes=3) as pool: # 병렬 프로세스 수 설정
        pool.map(process_single_image, args)

    print("\n[ALL IMAGES PROCESSED AND KEYWORDS INSERTED]")

if __name__ == "__main__":
    main()