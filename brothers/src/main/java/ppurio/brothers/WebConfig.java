package ppurio.brothers;

import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.ViewControllerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    // React 라우팅 설정
    @Override
    public void addViewControllers(ViewControllerRegistry registry) {
        registry.addViewController("/{spring:[^\\.]*}").setViewName("forward:/index.html");
    }

    // CORS 설정
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurer() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                // /api/submit-text 엔드포인트에 대해 CORS 허용
                registry.addMapping("/api/submit-text")
                        .allowedOrigins(
                                "http://54.252.153.150:8080", // 퍼블릭 IP (Spring Boot)
                                "http://54.252.153.150:3000", // 퍼블릭 IP (React 개발 서버)
                                "http://localhost:3000"      // 로컬 테스트용
                        )
                        .allowedMethods("GET", "POST", "OPTIONS") // 허용할 메서드
                        .allowedHeaders("*")
                        .allowCredentials(true);

                // /api/images/** 엔드포인트에 대해 CORS 허용
                registry.addMapping("/api/images/**")
                        .allowedOrigins(
                                "http://54.252.153.150:8080", // 퍼블릭 IP (Spring Boot)
                                "http://54.252.153.150:3000", // 퍼블릭 IP (React 개발 서버)
                                "http://localhost:3000"      // 로컬 테스트용
                        )
                        .allowedMethods("GET", "OPTIONS") // 허용할 메서드
                        .allowedHeaders("*")
                        .allowCredentials(true);
            }
        };
    }
}
