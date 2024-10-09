package ppurio.brothers;

import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public class ImageSender {

    public void sendImageToDomain(String imagePath, String targetUrl) throws IOException {
        // 이미지 파일 읽기
        Path path = Paths.get(imagePath);
        byte[] imageBytes = Files.readAllBytes(path);

        // 바디에 이미지 데이터 추가
        ByteArrayResource resource = new ByteArrayResource(imageBytes) {
            @Override
            public String getFilename() {
                return path.getFileName().toString(); // 원래 파일 이름을 반환
            }
        };

        // MultiValueMap을 사용하여 multipart/form-data 요청 본문 구성
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("image", resource);

        // HTTP 요청 헤더 설정
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        // HttpEntity 객체 생성
        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

        // RestTemplate을 사용해 이미지 전송
        RestTemplate restTemplate = new RestTemplate();

        // 예외 처리를 하지 않고 응답을 바로 받기
        ResponseEntity<String> response = restTemplate.exchange(
                targetUrl,
                HttpMethod.POST,
                requestEntity,
                String.class
        );

        // 응답 상태 코드와 바디를 출력
        System.out.println("Response Status Code: " + response.getStatusCode());
        System.out.println("Response Body: " + response.getBody());
    }
}
