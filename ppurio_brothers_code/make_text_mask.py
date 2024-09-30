import cv2
import pytesseract
from pytesseract import Output

# 이미지 파일 로드
image_path = 'ppurio_brothers_backup/image/mask/imgage_test2-mask.png'  # 처리할 이미지 경로
image = cv2.imread(image_path)

# 1. 원본 이미지 출력
cv2.imshow('Original Image', image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 2. 이미지를 흑백으로 변환 (OCR 성능 향상을 위해)
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 흑백 이미지 출력
cv2.imshow('Gray Image', gray_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 3. Tesseract를 사용하여 이미지에서 텍스트 영역을 감지
d = pytesseract.image_to_data(gray_image, output_type=Output.DICT)

# 원본 이미지 복사본을 생성 (텍스트 영역만 그리기 위한 이미지)
image_with_boxes = image.copy()

# 텍스트 영역 필터링을 위한 기준 (너무 큰 영역을 필터링)
max_width = image.shape[1] * 0.9  # 전체 이미지의 90%보다 큰 텍스트 영역 무시
max_height = image.shape[0] * 0.9  # 전체 이미지의 90%보다 큰 텍스트 영역 무시

# 4. 감지된 텍스트 영역에 사각형 그리기 (너무 큰 텍스트 영역 무시)
n_boxes = len(d['level'])
for i in range(n_boxes):
    (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
    
    # 텍스트 영역이 너무 크면 무시
    if w < max_width and h < max_height:
        # 텍스트 영역을 빨간색 사각형으로 표시
        cv2.rectangle(image_with_boxes, (x, y), (x + w, y + h), (0, 0, 255), 2)

# 5. 감지된 텍스트에 사각형이 그려진 이미지 출력
cv2.imshow('Text Detection (with Rectangles)', image_with_boxes)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 6. 흰색으로 텍스트 영역 마스킹 (필터링된 텍스트 영역에만 적용)
for i in range(n_boxes):
    (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
    
    # 텍스트 영역이 너무 크면 무시
    if w < max_width and h < max_height:
        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 255), -1)  # 흰색으로 마스킹

# 7. 텍스트가 흰색으로 마스킹된 이미지 출력
cv2.imshow('Masked Image', image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 8. 결과 이미지를 저장
output_image_path = 'ppurio_brothers_backup/image/temp/test-mask-revert.png'
cv2.imwrite(output_image_path, image)

print(f"처리된 이미지가 '{output_image_path}'에 저장되었습니다.")