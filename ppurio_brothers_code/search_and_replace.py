import requests

API_KEY = "MyAPIKEY"

response = requests.post(
    f"https://api.stability.ai/v2beta/stable-image/edit/search-and-replace",
    headers={
        "authorization": f"Bearer {API_KEY}",
        "accept": "image/*"
    },
    files={
        "image": open("ppurio_brothers_backup/image/origin_image/Image_test2.png", "rb")
    },
    data={
        "prompt": "a blank area without any text",
        "search_prompt": "text",
        "output_format": "png",
    },
)

if response.status_code == 200:
    with open("ppurio_brothers_backup/image/mask/image_test2-mask-replace.png", 'wb') as file:
        file.write(response.content)
else:
    raise Exception(str(response.json()))