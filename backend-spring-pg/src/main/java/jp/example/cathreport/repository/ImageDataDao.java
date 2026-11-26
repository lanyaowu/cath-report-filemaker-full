package jp.example.cathreport.repository;

import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import jp.example.cathreport.api.CathReport;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;

/**
 * 画像本体（table: report_image_data）の読み書き。
 * API では data URL（data:&lt;mime&gt;;base64,...）、DB では bytea（デコード済みバイナリ）。
 * レポート一覧の取得ではこのテーブルを読まないため、画像が多くても一覧は軽い。
 */
@Repository
public class ImageDataDao {
  private final JdbcTemplate jdbc;

  public ImageDataDao(JdbcTemplate jdbc) {
    this.jdbc = jdbc;
  }

  /** image_id → data URL */
  public Map<String, String> load(String reportId) {
    Map<String, String> out = new HashMap<>();
    jdbc.query("SELECT image_id, mime_type, data FROM report_image_data WHERE report_id = ?",
        rs -> {
          out.put(rs.getString(1), toDataUrl(rs.getString(2), rs.getBytes(3)));
        },
        reportId);
    return out;
  }

  /**
   * レポートの画像本体を同期する。
   * ・dataUrl のある画像は登録/更新（内容が同じなら書き込まない）
   * ・dataUrl が空の画像は既存の本体を維持
   * ・レポートから外された画像の本体は削除
   */
  public void sync(String reportId, List<CathReport.Image> images) {
    Set<String> keep = new HashSet<>();
    List<Object[]> upserts = new ArrayList<>();
    for (CathReport.Image img : images) {
      if (img == null || img.id == null) continue;
      keep.add(img.id);
      if (img.dataUrl == null || img.dataUrl.isBlank()) continue;
      Decoded d = decode(img.dataUrl, img.mimeType);
      upserts.add(new Object[] {reportId, img.id, d.mime, d.bytes});
    }
    List<String> existing = jdbc.queryForList("SELECT image_id FROM report_image_data WHERE report_id = ?", String.class, reportId);
    List<Object[]> deletes = new ArrayList<>();
    for (String id : existing) if (!keep.contains(id)) deletes.add(new Object[] {reportId, id});
    if (!deletes.isEmpty()) jdbc.batchUpdate("DELETE FROM report_image_data WHERE report_id = ? AND image_id = ?", deletes);
    if (!upserts.isEmpty()) {
      jdbc.batchUpdate("""
          INSERT INTO report_image_data (report_id, image_id, mime_type, data, updated_at)
          VALUES (?, ?, ?, ?, now())
          ON CONFLICT (report_id, image_id) DO UPDATE
            SET mime_type = EXCLUDED.mime_type, data = EXCLUDED.data, updated_at = now()
            WHERE report_image_data.data IS DISTINCT FROM EXCLUDED.data
               OR report_image_data.mime_type IS DISTINCT FROM EXCLUDED.mime_type
          """, upserts);
    }
  }

  record Decoded(String mime, byte[] bytes) {}

  /** data URL を MIME とバイナリに分解（base64 / URL エンコードの両方に対応） */
  static Decoded decode(String dataUrl, String fallbackMime) {
    if (!dataUrl.startsWith("data:")) throw bad("画像データが data URL 形式ではありません");
    int comma = dataUrl.indexOf(',');
    if (comma < 0) throw bad("画像データ（data URL）が不正です");
    String meta = dataUrl.substring(5, comma);
    String payload = dataUrl.substring(comma + 1);
    boolean base64 = meta.endsWith(";base64");
    String mime = (base64 ? meta.substring(0, meta.length() - 7) : meta).split(";")[0].trim();
    if (mime.isEmpty()) mime = fallbackMime == null || fallbackMime.isBlank() ? "application/octet-stream" : fallbackMime;
    try {
      byte[] bytes = base64
          ? Base64.getMimeDecoder().decode(payload)
          : URLDecoder.decode(payload.replace("+", "%2B"), StandardCharsets.UTF_8).getBytes(StandardCharsets.UTF_8);
      return new Decoded(mime, bytes);
    } catch (IllegalArgumentException e) {
      throw bad("画像データの base64 が不正です");
    }
  }

  static String toDataUrl(String mime, byte[] bytes) {
    return "data:" + mime + ";base64," + Base64.getEncoder().encodeToString(bytes);
  }

  private static ResponseStatusException bad(String msg) {
    return new ResponseStatusException(HttpStatus.BAD_REQUEST, msg);
  }
}
