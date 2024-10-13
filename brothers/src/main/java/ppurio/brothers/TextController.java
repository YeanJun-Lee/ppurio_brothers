package ppurio.brothers;

import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api")
public class TextController {

    @PostMapping("/submit-text")
    public String receiveText(@RequestBody Map<String, String> payload) {
        // JSON에서 "message"라는 필드를 추출
        String message = payload.get("message");
        System.out.println("Received text: " + message);
        return "Text received: " + message;
    }

}