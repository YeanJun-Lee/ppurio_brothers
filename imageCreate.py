import os
import requests
import json
import openai

# OpenAI API 초기화
client = openai.OpenAI(
    api_key='my-key'
)

# 스타일 ID와 그림체 및 폰트 매핑
STYLE_MAP = {
    "style1": {
        "art_style": "a modern and professional style with clean, sleek design elements",
        "font": "Noto Sans KR"
    },
    "style2": {
        "art_style": "a classic and elegant style featuring serif fonts and soft colors",
        "font": "Nanum Myeongjo"
    },
    "style3": {
        "art_style": "an eco-friendly style with earthy tones and natural elements",
        "font": "Spoqa Han Sans"
    },
    "style4": {
        "art_style": "a warm and friendly local event style with cozy, inviting visuals",
        "font": "배민 한나는 열한살"
    },
    "style5": {
        "art_style": "a practical, information-focused style with clear, concise visuals",
        "font": "Nanum Gothic"
    },
    "style6": {
        "art_style": "a viral social media style with bold, eye-catching visuals",
        "font": "Do Hyeon"
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

# 실행 코드
if __name__ == "__main__":
    # 사용자 입력 받기
    user_input = input("고객님의 이벤트 정보를 입력해 주세요: ")
    brand_input = input("브랜드명이 있으면 입력해 주세요 (없으면 엔터): ")
    selected_style = input("선택한 스타일 ID를 입력하세요 (예: style1, style2, ...): ")

    # 프론트엔드에서 입력받은 키워드 (사용자가 입력하지 않으면 빈 리스트)
    user_selected_keywords = input("사용자가 선택한 키워드(쉼표로 구분, 최대 3개 이하)를 입력하세요: ").split(",")
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

    # DALL·E로 포스터 생성
    poster_image_url = generate_poster_with_dalle(dalle_prompt, art_style)

    # 이미지와 JSON 데이터 저장
    OUTPUT_DIR = "./output"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    poster_output_path = os.path.join(OUTPUT_DIR, "poster.png")
    metadata_output_path = os.path.join(OUTPUT_DIR, "data.json")

    # 이미지 저장
    save_image_as_png(poster_image_url, poster_output_path)

    # JSON 데이터 저장
    save_data_as_json(recommended_font, top_keywords, metadata_output_path)

    print("Image and JSON files are ready.")
