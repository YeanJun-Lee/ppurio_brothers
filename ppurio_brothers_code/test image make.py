import openai
client = openai.OpenAI(api_key = 'School APIKey')
'''
사용 메세지

2024년 9월 24일, 우리 대학의 자랑스러운 체육대전이 개최됩니다! 이번 체육대전은 학생 여러분의 열정과 팀워크를 발휘할 수 있는 멋진 기회입니다. 다양한 종목에서 경쟁하며, 상품도 걸려 있으니 많은 참여 부탁드립니다.

체육대전 주요 정보:
일시: 2024년 9월 24일
장소: 한성대학교
참여 종목: 축구, 농구, 피구, 배드민턴, 탁구
상품: 치킨

체육대전은 단순한 경쟁을 넘어, 서로의 우정을 다지고, 즐거운 추억을 만드는 자리입니다. 여러분의 많은 참여와 응원을 부탁드립니다! 함께 즐거운 시간을 만들어 봅시다
'''
PROMPT = "A vibrant promotional poster for a university sports event happening on September 24, 2024. The poster features dynamic and energetic elements representing various sports like soccer, basketball, dodgeball, badminton, and table tennis. The text highlights key event details: ‘Date: September 24, 2024,’ ‘Location: Hansung University,’ and ‘Prizes: Chicken.’ The background is colorful and lively, with students cheering, playing sports, and forming strong team bonds, evoking a sense of teamwork and excitement. The theme emphasizes friendship, fun, and competition. The university logo and event title are prominently displayed."

response = client.images.generate(
    prompt=PROMPT,
    model="dall-e-3",
    n=1,
    size="1024x1024",
    quality="hd",
)

image_url = response.data[0].url
print(f"Generated Image URL: {image_url}")