package jp.example.cathreport.service;

import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeParseException;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

/** API（文字列）と DB（DATE / TIMESTAMPTZ / boolean）の値変換 */
final class Conv {
  private Conv() {}

  private static final ZoneId LOCAL = ZoneId.of("Asia/Tokyo");

  /** "YYYY-MM-DD"（または日時文字列の日付部分）→ LocalDate。空は null、不正は 400 */
  static LocalDate date(String s, String field) {
    if (s == null || s.isBlank()) return null;
    String v = s.trim().replace('/', '-');
    try {
      return LocalDate.parse(v.length() > 10 ? v.substring(0, 10) : v);
    } catch (DateTimeParseException e) {
      throw new ResponseStatusException(HttpStatus.BAD_REQUEST, field + " の日付形式が不正です: " + s);
    }
  }

  /** 集計用の展開列向け：不正値は例外にせず null */
  static LocalDate dateLenient(Object o) {
    if (!(o instanceof String s) || s.isBlank()) return null;
    try {
      return date(s, "");
    } catch (ResponseStatusException e) {
      return null;
    }
  }

  static String date(LocalDate d) {
    return d == null ? "" : d.toString();
  }

  /** ISO 日時 → Instant。タイムゾーンなしは日本時間とみなす。空は null、不正は 400 */
  static Instant instant(String s, String field) {
    if (s == null || s.isBlank()) return null;
    try {
      return OffsetDateTime.parse(s.trim()).toInstant();
    } catch (DateTimeParseException e) {
      try {
        return LocalDateTime.parse(s.trim()).atZone(LOCAL).toInstant();
      } catch (DateTimeParseException e2) {
        throw new ResponseStatusException(HttpStatus.BAD_REQUEST, field + " の日時形式が不正です: " + s);
      }
    }
  }

  static String instant(Instant i) {
    return i == null ? null : i.toString();
  }

  static boolean bool(Boolean b) {
    return Boolean.TRUE.equals(b);
  }

  static String str(Object o) {
    return o == null ? null : o.toString();
  }

  @SuppressWarnings("unchecked")
  static Map<String, Object> map(Object o) {
    return o instanceof Map<?, ?> m ? (Map<String, Object>) m : Map.of();
  }

  static boolean truthy(Object o) {
    return o instanceof Boolean b ? b : o instanceof String s && (s.equalsIgnoreCase("true") || s.equals("1"));
  }
}
