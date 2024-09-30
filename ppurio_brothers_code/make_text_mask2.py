import cv2
from craft_text_detector import Craft
import numpy as np
from torchvision.models import vgg16_bn

# CRAFT 모델 초기화
craft = Craft(output_dir='ppurio_brothers_backup/image/mask/', crop_type="box", cuda=False)

# vgg16_bn 모델 불러오기 (pretrained=True로 사전 학습된 가중치 사용)
model = vgg16_bn(pretrained=True)

# 이미지 파일 로드
image_path = 'ppurio_brothers_backup/image/origin_image/test.png'  # 처리할 이미지 경로
image = cv2.imread(image_path)

# 이미지 로드 확인
if image is None:
    raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {image_path}")

# 1. 원본 이미지 출력
cv2.imshow('Original Image', image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 2. CRAFT 모델을 사용하여 이미지에서 텍스트 감지
predictions = craft.detect_text(image)

# 감지된 텍스트 영역 표시를 위한 이미지 복사본
image_with_boxes = image.copy()

# 3. 감지된 텍스트 영역에 사각형 그리기
for box in predictions['boxes']:
    x1, y1 = int(box[0][0]), int(box[0][1])
    x2, y2 = int(box[2][0]), int(box[2][1])
    
    # 빨간색 사각형 그리기 (텍스트 감지 영역 표시)
    cv2.rectangle(image_with_boxes, (x1, y1), (x2, y2), (0, 0, 255), 2)

# 감지된 텍스트에 사각형이 그려진 이미지 출력
cv2.imshow('Text Detection (with Rectangles)', image_with_boxes)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 4. 텍스트 영역을 흰색으로 마스킹 (사각형 그린 부분 마스킹)
for box in predictions['boxes']:
    x1, y1 = int(box[0][0]), int(box[0][1])
    x2, y2 = int(box[2][0]), int(box[2][1])

    # 흰색 사각형 그리기 (텍스트 영역 마스킹)
    cv2.rectangle(image, (x1, y1), (x2, y2), (255, 255, 255), -1)  # -1은 내부를 채우는 의미

# 5. 텍스트가 흰색으로 마스킹된 이미지 출력
cv2.imshow('Masked Image', image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 6. 결과 이미지를 저장
output_image_path = 'test-mask.png'
cv2.imwrite(output_image_path, image)

print(f"처리된 이미지가 '{output_image_path}'에 저장되었습니다.")

# CRAFT 모델 메모리 해제
craft.unload_craftnet_model()
craft.unload_refinenet_model()