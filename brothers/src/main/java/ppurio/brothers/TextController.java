package ppurio.brothers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.MalformedURLException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = {
        "http://223.194.129.35:3000",  // 이전 IP
        "http://223.194.157.135:3000", // 이전 IP
        "http://223.194.131.243:3000",
        "http://192.168.109.6:3000",
        "http://54.252.153.150:8080"// 현재 IP
})
public class TextController {

    @Autowired
    private PythonScriptService pythonScriptService;

    // POST 요청을 처리하여 텍스트를 받아 Python 스크립트 실행
    @PostMapping("/submit-text")
    public Map<String, Object> receiveText(@RequestBody Map<String, Object> payload) {
        // JSON에서 "message", "keywords", "brand", "style" 필드를 추출
        String message = (String) payload.get("message");
        List<String> keywords = (List<String>) payload.get("keywords"); // 키워드 배열
        String brandKeyword = (String) payload.get("brandKeyword");
        String style = (String) payload.get("style");
        System.out.println("받은 메세지: " + message);
        System.out.println("받은 키워드: " + keywords);
        System.out.println("받은 브랜드: " + brandKeyword);
        System.out.println("받은 스타일: " + style);

        // Python 스크립트 실행 (실제로 실행은 하지만 결과를 URL과 연결하지 않음)
        Map<String, Object> pythonInput = new HashMap<>();
        pythonInput.put("message", message);
        pythonInput.put("keywords", keywords);
        pythonInput.put("brand", brandKeyword);
        pythonInput.put("style", style);

        pythonScriptService.executePythonScript(pythonInput);

        // 하드코딩된 이미지 URL 반환
        List<String> imageUrls = List.of(
                "http://54.252.153.150:8080/api/images/final_poster_1.png",
                "http://54.252.153.150:8080/api/images/final_poster_2.png",
                "http://54.252.153.150:8080/api/images/final_poster_3.png"
        );

        // 응답 생성
        Map<String, Object> response = new HashMap<>();
        response.put("response", "Text received and processed");
        response.put("imageUrls", imageUrls); // 하드코딩된 URL 반환
        System.out.println("Response: " + response);

        return response;
    }

    // 이미지 파일 반환 API
    @GetMapping("/images/{filename}")
    public ResponseEntity<Resource> getImage(@PathVariable String filename) {
        try {
            // 이미지 파일 경로 설정
            Path file = Paths.get("/home/ec2-user/images/final_output/").resolve(filename);
            Resource resource = new UrlResource(file.toUri());
            if (resource.exists() || resource.isReadable()) {
                return ResponseEntity.ok()
                        .contentType(MediaType.IMAGE_PNG) // PNG 형식으로 응답
                        .body(resource);
            } else {
                throw new RuntimeException("Could not read the file!");
            }
        } catch (MalformedURLException e) {
            throw new RuntimeException("Error: " + e.getMessage());
        }
    }
}