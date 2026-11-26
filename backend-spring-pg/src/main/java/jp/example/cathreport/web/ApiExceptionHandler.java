package jp.example.cathreport.web;

import java.util.Map;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.server.ResponseStatusException;

/** エラーを {"error": "..."} 形式で返す（Node 版・MongoDB 版と同一形式） */
@RestControllerAdvice
public class ApiExceptionHandler {
  private static final Logger log = LoggerFactory.getLogger(ApiExceptionHandler.class);

  @ExceptionHandler(ResponseStatusException.class)
  public ResponseEntity<Map<String, String>> status(ResponseStatusException e) {
    return ResponseEntity.status(e.getStatusCode()).body(Map.of("error", e.getReason() == null ? e.getStatusCode().toString() : e.getReason()));
  }

  @ExceptionHandler(MethodArgumentNotValidException.class)
  public ResponseEntity<Map<String, String>> invalid(MethodArgumentNotValidException e) {
    String msg = e.getBindingResult().getFieldErrors().stream().map(f -> f.getField() + ": " + f.getDefaultMessage()).collect(Collectors.joining(", "));
    return ResponseEntity.badRequest().body(Map.of("error", "入力エラー: " + msg));
  }

  @ExceptionHandler(HttpMessageNotReadableException.class)
  public ResponseEntity<Map<String, String>> unreadable(HttpMessageNotReadableException e) {
    return ResponseEntity.badRequest().body(Map.of("error", "JSON の形式が不正です"));
  }

  /** 同時更新（@Version 不一致） */
  @ExceptionHandler(OptimisticLockingFailureException.class)
  public ResponseEntity<Map<String, String>> conflict(OptimisticLockingFailureException e) {
    return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("error", "他の端末で更新されています。再読み込みしてください"));
  }

  /** 一意制約・外部キー・CHECK 制約違反 */
  @ExceptionHandler(DataIntegrityViolationException.class)
  public ResponseEntity<Map<String, String>> integrity(DataIntegrityViolationException e) {
    String cause = e.getMostSpecificCause().getMessage();
    log.warn("データ整合性エラー: {}", cause);
    return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("error", "データ整合性エラー: " + firstLine(cause)));
  }

  @ExceptionHandler(Exception.class)
  public ResponseEntity<Map<String, String>> other(Exception e) {
    log.error("想定外のエラー", e); // 詳細はログにだけ出し、利用者には一般的なメッセージを返す
    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", "サーバーでエラーが発生しました（詳細はサーバーのログを確認してください）"));
  }

  private static String firstLine(String s) {
    if (s == null) return "";
    int i = s.indexOf('\n');
    return i < 0 ? s : s.substring(0, i);
  }
}
