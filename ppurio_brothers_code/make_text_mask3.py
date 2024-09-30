import cv2
import numpy as np

# 이미지 읽기
image = cv2.imread('ppurio_brothers_backup/image/mask/imgage_test2-mask.png')

# 원본 이미지 표시
cv2.imshow('Original Image', image)
cv2.waitKey(0)

# 그레이스케일 변환
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 그레이스케일 이미지 표시
cv2.imshow('Grayscale Image', gray)
cv2.waitKey(0)

# 이진화 (임계값 조정)
_, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

# 이진화된 이미지 표시
cv2.imshow('Binary Image', binary)
cv2.waitKey(0)

# 모폴로지 연산 적용 (잡음 제거)
kernel = np.ones((3, 3), np.uint8)
binary_morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

# 모폴로지 연산 결과 이미지 표시
cv2.imshow('Morphology Image', binary_morph)
cv2.waitKey(0)

# 윤곽선 감지
contours, _ = cv2.findContours(binary_morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 윤곽선이 감지된 이미지 복사본 생성
contour_image = image.copy()
cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 2)

# 윤곽선이 그려진 이미지 표시
cv2.imshow('Contour Image', contour_image)
cv2.waitKey(0)

# 일정 크기 이상의 윤곽선만 사용
min_area = 100  # 조정 가능
filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]

# 필터링된 윤곽선 그리기
filtered_contour_image = image.copy()
cv2.drawContours(filtered_contour_image, filtered_contours, -1, (0, 255, 0), 2)

# 필터링된 윤곽선 이미지 표시
cv2.imshow('Filtered Contour Image', filtered_contour_image)
cv2.waitKey(0)

# 마스크 생성
mask = np.zeros_like(image)
cv2.drawContours(mask, filtered_contours, -1, (255, 255, 255), thickness=cv2.FILLED)

# 마스크 이미지 표시
cv2.imshow('Mask Image', mask)
cv2.waitKey(0)

# 마스크 저장
cv2.imwrite('ppurio_brothers_backup/image/temp/imgage_test2-mask-revert.png', mask)

# 모든 창 닫기
cv2.destroyAllWindows()