package jp.example.cathreport.web;

import java.util.Map;
import java.util.stream.Collectors;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.server.ResponseStatusException;

/** エラーを {"error": "..."} 形式で返す（Node 版と同一形式） */
@RestControllerAdvice
public class ApiExceptionHandler {
  @ExceptionHandler(ResponseStatusException.class)
  public ResponseEntity<Map<String, String>> status(ResponseStatusException e) {
    return ResponseEntity.status(e.getStatusCode()).body(Map.of("error", e.getReason() == null ? e.getStatusCode().toString() : e.getReason()));
  }

  @ExceptionHandler(MethodArgumentNotValidException.class)
  public ResponseEntity<Map<String, String>> invalid(MethodArgumentNotValidException e) {
    String msg = e.getBindingResult().getFieldErrors().stream().map(f -> f.getField() + ": " + f.getDefaultMessage()).collect(Collectors.joining(", "));
    return ResponseEntity.badRequest().body(Map.of("error", "入力エラー: " + msg));
  }

  @ExceptionHandler(org.springframework.http.converter.HttpMessageNotReadableException.class)
  public ResponseEntity<Map<String, String>> unreadable(Exception e) {
    return ResponseEntity.badRequest().body(Map.of("error", "JSON の形式が不正です"));
  }

  /** 想定外のエラー：詳細はログにだけ出し、利用者には一般的なメッセージを返す */
  @ExceptionHandler(Exception.class)
  public ResponseEntity<Map<String, String>> other(Exception e) {
    org.slf4j.LoggerFactory.getLogger(ApiExceptionHandler.class).error("想定外のエラー", e);
    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "サーバーでエラーが発生しました（詳細はサーバーのログを確認してください）"));
  }
}
