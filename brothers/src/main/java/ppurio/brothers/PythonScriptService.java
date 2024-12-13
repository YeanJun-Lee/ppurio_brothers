package ppurio.brothers;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;

import java.io.*;
import java.util.Map;
import java.util.logging.Logger;

@Service
public class PythonScriptService {
    private static final Logger logger = Logger.getLogger(PythonScriptService.class.getName());

    // JSON 데이터를 Python 스크립트에 전달하는 메소드
    public String executePythonScript(Map<String, Object> jsonData) {
        String result = "";
        try {
            // JSON 데이터를 파일로 저장
            ObjectMapper objectMapper = new ObjectMapper();
            String jsonFilePath = "/home/ec2-user/prompt/prompt.json";
            File jsonFile = new File(jsonFilePath);

            // 파일 생성 및 JSON 데이터 쓰기
            try (FileWriter fileWriter = new FileWriter(jsonFile)) {
                objectMapper.writeValue(fileWriter, jsonData);
            }

            // Python 스크립트를 실행할 명령어에 JSON 파일 경로를 인자로 추가
            ProcessBuilder processBuilder = new ProcessBuilder(
                    "/usr/bin/python3",
                    "/home/ec2-user/ppurio_brothers_code/ppurio_brothers_refactored.py"
            );

            // 환경 변수 추가
            processBuilder.environment().put("OPENAI_API_KEY", System.getenv("OPENAI_API_KEY"));
            processBuilder.environment().put("STABLE_API_KEY", System.getenv("STABLE_API_KEY"));

            processBuilder.redirectErrorStream(true); // 표준 에러를 표준 출력으로 병합

            // 프로세스 실행
            Process process = processBuilder.start();

            // 스크립트 실행 결과 읽기
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder output = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }

            // 프로세스 종료 시까지 대기
            int exitCode = process.waitFor();
            if (exitCode == 0) {
                result = output.toString().trim();  // Python 스크립트의 최종 출력
                logger.info("Script executed successfully, output: " + result);
            } else {
                logger.warning("Python script exited with code: " + exitCode);
            }

        } catch (Exception e) {
            e.printStackTrace();
            result = "Error occurred: " + e.getMessage();
        }

        return result;  // Python에서 반환한 이미지 경로 또는 다른 출력
    }
}
