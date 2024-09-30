import pytesseract
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt

# 이미지를 화면에 표시하는 함수
def show_image(img, title="Image"):
    plt.imshow(img)
    plt.title(title)
    plt.axis('off')  # 축 제거
    plt.show()

# 이미지 불러오기
image_path = "ppurio_brothers_backup/image/mask/Image_test2-mask-replace.png"
image = Image.open(image_path)

# Tesseract 설정을 이용해 인식 품질 높이기
custom_config = r'--oem 3 --psm 6'  # 3: LSTM 기반 OCR, 6: 텍스트 블록 단위 분석

# 언어 설정 (영어)
text = pytesseract.image_to_string(image, lang='eng', config=custom_config)

# 텍스트 영역 찾기 (Tesseract OCR 사용)
boxes = pytesseract.image_to_boxes(image)

# 원본 이미지 보여주기 (처리 전)
show_image(image, title="Original Image")

# 원본 이미지에 텍스트가 있는 부분을 흰색 박스로 덮기 위한 작업
draw = ImageDraw.Draw(image)

# 여백 설정 (텍스트 상자 주위에 더 넓은 영역을 덮기 위해)
padding = 5  # 5 픽셀의 여백을 추가

# 텍스트 영역을 흰색으로 덮는 과정
for box in boxes.splitlines():
    b = box.split(' ')
    x1, y1, x2, y2 = int(b[1]), int(b[2]), int(b[3]), int(b[4])
    
    # Tesseract 좌표는 이미지의 왼쪽 아래가 (0, 0)이므로 좌표계를 반전
    y1 = image.height - y1
    y2 = image.height - y2
    
    # 여백 추가하여 박스 영역 확장
    draw.rectangle([x1 - padding, y2 - padding, x2 + padding, y1 + padding], fill="white")

# 결과 이미지 보여주기 (최종 결과)
show_image(image, title="Final Image with Mask")

# 결과 저장
image.save("ppurio_brothers_backup/image/temp/imgage_test2-mask-replace.png")