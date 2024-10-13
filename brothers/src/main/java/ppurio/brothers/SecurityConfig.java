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
                .csrf(csrf -> csrf.disable() // CSRF 보호 비활성화 (개발 중일 때만)
                )
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/upload").permitAll() // '/upload' 경로에 대한 인증 허용
                        .anyRequest().authenticated() // 나머지 요청은 인증 필요
                )
                .formLogin(form -> form
                        .loginPage("/login") // 로그인 페이지 경로
                        .permitAll() // 모든 사용자에게 로그인 페이지 접근 허용
                );

        return http.build();
    }
}
