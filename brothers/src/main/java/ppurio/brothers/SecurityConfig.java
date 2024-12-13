package ppurio.brothers;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .csrf(csrf -> csrf.disable()) // CSRF 보호 비활성화
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/", "/index.html", "/static/**", "/favicon.ico").permitAll() // React 정적 파일 접근 허용
                        .requestMatchers("/api/**", "/images/**", "/upload").permitAll() // API와 기타 경로 인증 없이 접근 허용
                        .anyRequest().permitAll() // 나머지 모든 요청도 인증 없이 접근 허용
                )
                .formLogin(form -> form.disable()) // 로그인 폼 비활성화
                .httpBasic(basic -> basic.disable()); // HTTP Basic 인증 비활성화

        return http.build();
    }
}
