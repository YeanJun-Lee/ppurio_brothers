package ppurio.brothers;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class PpurioApplication {

	public static void main(String[] args) {
		// Spring Boot 애플리케이션 실행
		SpringApplication.run(PpurioApplication.class, args);

		// ImageSender 인스턴스 생성
		ImageSender imageSender = new ImageSender();

		// 이미지 파일 경로와 전송할 도메인 URL 설정
		String imagePath = "C:/free/ImagePost.png";  // 실제 이미지 파일 경로로 변경하세요.
		String targetUrl = "http://localhost:8080/upload";  // 서버의 업로드 URL 설정

		try {
			// 이미지 전송 메서드 호출
			imageSender.sendImageToDomain(imagePath, targetUrl);
		} catch (Exception e) {
			// 이미지 전송 중 예외가 발생한 경우 스택 트레이스 출력
			e.printStackTrace();
		}
	}
}
