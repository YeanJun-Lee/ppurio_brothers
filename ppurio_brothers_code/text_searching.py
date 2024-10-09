import cv2
import easyocr
import matplotlib.pyplot as plt

# EasyOCR reader 객체 생성 (여러 언어를 지원, 'ko'는 한국어)
reader = easyocr.Reader(['en', 'ko'])

# 이미지 불러오기
image_path = 'ppurio_brothers_backup/image/origin_image/donghak.png'
image = cv2.imread(image_path)

# 텍스트 감지 (박스와 텍스트 내용 및 confidence 반환)
results = reader.readtext(image_path)

# 이미지에 네모 박스 그리기
for (bbox, text, prob) in results:
    # 박스 좌표 추출
    (top_left, top_right, bottom_right, bottom_left) = bbox
    top_left = tuple(map(int, top_left))
    bottom_right = tuple(map(int, bottom_right))

    # 텍스트 영역에 네모 박스 그리기
    cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)

    # 인식된 텍스트 표시
    cv2.putText(image, text, (top_left[0], top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

# 결과 이미지 출력
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.axis('off')
plt.show()