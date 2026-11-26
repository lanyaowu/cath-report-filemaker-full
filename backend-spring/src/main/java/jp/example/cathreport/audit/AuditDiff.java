package jp.example.cathreport.audit;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 監査ログ：保存前後の JSON を比べて、変わった項目（パス・変更前・変更後）を取り出す。
 *
 * <p>全バックエンド・Thymeleaf 版で同じ規則（frontend/src/audit/diff.ts・backend-node/src/auditDiff.ts・
 * Thymeleaf 版の tools/review/engine.js。変える時は全部そろえる）。
 * <ul>
 *   <li>JSON を「パス → 文字列」に平らにして比べる（配列は番号：pci.lesions.0.target）</li>
 *   <li>記録しない：先頭の version・updatedAt・createdAt・history・_id、どこにあっても dataUrl（画像本体）</li>
 *   <li>null・false・項目なしは空（""）と同じとみなす</li>
 *   <li>値は 200 文字までに切る。1 回の保存で記録するのは 1,000 項目まで</li>
 * </ul>
 */
public final class AuditDiff {
  private AuditDiff() {}

  public record Change(String path, String before, String after) {}

  static final Set<String> EXCLUDE_TOP = Set.of("version", "updatedAt", "createdAt", "history", "_id");
  static final Set<String> EXCLUDE_KEY = Set.of("dataUrl");
  public static final int MAX_VALUE = 200;
  public static final int MAX_CHANGES = 1000;

  public static Map<String, String> flatten(JsonNode n) {
    Map<String, String> out = new LinkedHashMap<>();
    flatten(n, "", out);
    return out;
  }

  private static void flatten(JsonNode n, String prefix, Map<String, String> out) {
    if (n == null || n.isNull() || n.isMissingNode()) {
      if (!prefix.isEmpty()) out.put(prefix, "");
      return;
    }
    if (n.isArray()) {
      for (int i = 0; i < n.size(); i++) flatten(n.get(i), prefix.isEmpty() ? String.valueOf(i) : prefix + "." + i, out);
      return;
    }
    if (n.isObject()) {
      Iterator<Map.Entry<String, JsonNode>> it = n.fields();
      while (it.hasNext()) {
        Map.Entry<String, JsonNode> e = it.next();
        String k = e.getKey();
        if (prefix.isEmpty() && EXCLUDE_TOP.contains(k)) continue;
        if (EXCLUDE_KEY.contains(k)) continue;
        flatten(e.getValue(), prefix.isEmpty() ? k : prefix + "." + k, out);
      }
      return;
    }
    if (prefix.isEmpty()) return;
    if (n.isBoolean()) out.put(prefix, n.booleanValue() ? "true" : "");
    else out.put(prefix, n.asText());
  }

  private static String cut(String s) {
    return s.length() > MAX_VALUE ? s.substring(0, MAX_VALUE) + "…" : s;
  }

  /** before が null なら新規（空でない項目だけが残る） */
  public static List<Change> diff(JsonNode before, JsonNode after) {
    Map<String, String> b = before == null ? Map.of() : flatten(before);
    Map<String, String> a = after == null ? Map.of() : flatten(after);
    List<Change> out = new ArrayList<>();
    for (String k : a.keySet()) add(out, k, b, a);
    for (String k : b.keySet()) if (!a.containsKey(k)) add(out, k, b, a);
    return out;
  }

  private static void add(List<Change> out, String path, Map<String, String> b, Map<String, String> a) {
    String x = b.getOrDefault(path, "");
    String y = a.getOrDefault(path, "");
    if (!x.equals(y) && out.size() < MAX_CHANGES) out.add(new Change(path, cut(x), cut(y)));
  }
}
