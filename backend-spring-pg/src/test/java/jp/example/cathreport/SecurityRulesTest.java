package jp.example.cathreport;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import jp.example.cathreport.security.AuthUser;
import jp.example.cathreport.security.PasswordHasher;
import jp.example.cathreport.security.Permission;
import jp.example.cathreport.security.ReportRules;
import jp.example.cathreport.security.TokenService;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

/** 認証・権限・業務ルール（Node.js 版 test/*.test.ts と同じ観点） */
class SecurityRulesTest {
  final ObjectMapper om = new ObjectMapper();
  final AuthUser doctor = new AuthUser("yamada", "山田 太郎", List.of("doctor"));
  final AuthUser secretary = new AuthUser("hisho", "秘書 花子", List.of("secretary"));
  final AuthUser viewer = new AuthUser("etsuran", "閲覧 用", List.of("viewer"));

  ObjectNode report(String status) {
    ObjectNode r = om.createObjectNode();
    r.put("id", "rp-1").put("patientRef", "pt-1").put("status", status).put("verified", false);
    r.putObject("header").put("studyDate", "2026-11-02").put("registrant", "山田 太郎");
    r.putObject("cathRecord").putObject("exam").put("diagnosis", "AP");
    r.putArray("history").addObject().put("at", "t0").put("by", "山田 太郎").put("action", "新規作成");
    return r;
  }

  @Test
  void password() {
    String h = PasswordHasher.hash("secret-1");
    assertThat(h).startsWith("pbkdf2_sha256$" + PasswordHasher.ITERATIONS + "$");
    assertThat(PasswordHasher.verify("secret-1", h)).isTrue();
    assertThat(PasswordHasher.verify("secret-2", h)).isFalse();
    assertThat(PasswordHasher.verify("x", "plain")).isFalse();
  }

  @Test
  void token() {
    TokenService t = new TokenService(om, "k1", 60);
    String token = t.issue(doctor).token();
    assertThat(t.verify(token)).isEqualTo(doctor);
    assertThat(new TokenService(om, "k2", 60).verify(token)).isNull();
    assertThat(t.verify(token + "x")).isNull();
    assertThat(t.verify("a.b.c")).isNull();
  }

  @Test
  void permissions() {
    assertThat(viewer.can(Permission.READ)).isTrue();
    assertThat(viewer.can(Permission.EDIT)).isFalse();
    assertThat(secretary.can(Permission.EDIT)).isTrue();
    assertThat(secretary.can(Permission.CONFIRM)).isFalse();
    assertThat(doctor.can(Permission.CONFIRM)).isTrue();
    assertThat(doctor.can(Permission.MASTERS)).isFalse();
  }

  @Test
  void roles() {
    ObjectNode old = report("入力中");
    assertThatThrownBy(() -> ReportRules.check(viewer, old, report("入力中"))).hasMessageContaining("編集");
    assertThatThrownBy(() -> ReportRules.check(secretary, old, report("確定"))).hasMessageContaining("確定");
    ObjectNode verified = report("入力中");
    verified.put("verified", true);
    assertThatThrownBy(() -> ReportRules.check(secretary, old, verified)).hasMessageContaining("照合");
    assertThatCode(() -> ReportRules.check(doctor, old, report("確定"))).doesNotThrowAnyException();
  }

  @Test
  void lock() {
    ObjectNode locked = report("確定");
    ObjectNode changed = report("確定");
    ((ObjectNode) changed.get("cathRecord").get("exam")).put("diagnosis", "OMI");
    assertThatThrownBy(() -> ReportRules.check(doctor, locked, changed))
        .isInstanceOf(ResponseStatusException.class).hasMessageContaining("確定済み");
    ObjectNode allowed = report("確定");
    allowed.put("verified", true).put("version", 9);
    ((ObjectNode) allowed.get("header")).put("registrant", "佐藤 健一");
    ((ArrayNode) allowed.get("history")).addObject().put("at", "t1").put("by", "x").put("action", "保存");
    assertThatCode(() -> ReportRules.check(doctor, locked, allowed)).doesNotThrowAnyException();
    ObjectNode unlock = changed.deepCopy();
    unlock.put("status", "入力中");
    assertThatCode(() -> ReportRules.check(doctor, locked, unlock)).doesNotThrowAnyException();
  }

  @Test
  void historyIsAppendOnly() {
    ObjectNode n = report("入力中");
    n.putArray("history");
    assertThatThrownBy(() -> ReportRules.check(doctor, report("入力中"), n)).hasMessageContaining("登録履歴");
  }

  @Test
  void version() {
    assertThat(ReportRules.nextVersion("レポート", false, null, null)).isZero();
    assertThat(ReportRules.nextVersion("レポート", true, 2L, 2L)).isEqualTo(3);
    assertThat(ReportRules.nextVersion("レポート", true, null, 0L)).isEqualTo(1);
    assertThatThrownBy(() -> ReportRules.nextVersion("レポート", true, 2L, 1L)).hasMessageContaining("他の端末");
    assertThatThrownBy(() -> ReportRules.nextVersion("患者", true, 2L, null)).hasMessageContaining("version が必要");
  }
}
