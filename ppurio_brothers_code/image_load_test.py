import cv2

# 이미지 경로 설정
image_path = 'test1.png'

# 이미지 불러오기
image = cv2.imread(image_path)

# 이미지가 제대로 불러와졌는지 확인
if image is None:
    raise Exception(f"이미지를 불러올 수 없습니다. 경로를 확인하세요: {image_path}")

# 이미지 출력
cv2.imshow('Loaded Image', image)
cv2.waitKey(0)
cv2.destroyAllWindows()