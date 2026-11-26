package jp.example.cathreport.config;

import jp.example.cathreport.security.ApiAuthInterceptor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
  @Value("${app.cors-origins}")
  private String[] origins;

  private final ApiAuthInterceptor auth;

  public WebConfig(ApiAuthInterceptor auth) {
    this.auth = auth;
  }

  @Override
  public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/api/**").allowedOrigins(origins).allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS");
  }

  /** /api/** はログインが必要（ApiAuthInterceptor） */
  @Override
  public void addInterceptors(InterceptorRegistry registry) {
    registry.addInterceptor(auth).addPathPatterns("/api/**");
  }
}
