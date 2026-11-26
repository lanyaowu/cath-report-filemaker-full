package jp.example.cathreport.security;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** ログインに続けて失敗した利用者を一定時間ロックする（既定：5 回で 15 分） */
public class LoginThrottle {
  private record Fail(int count, long until) {}

  private final Map<String, Fail> fails = new ConcurrentHashMap<>();
  private final int maxFailures;
  private final long lockMillis;

  public LoginThrottle(int maxFailures, int lockMinutes) {
    this.maxFailures = maxFailures;
    this.lockMillis = lockMinutes * 60_000L;
  }

  /** ロック中なら解除時刻（ms）、そうでなければ null */
  public Long lockedUntil(String username, long now) {
    Fail f = fails.get(username);
    return f != null && f.until > now ? f.until : null;
  }

  public void fail(String username, long now) {
    fails.compute(username, (k, f) -> {
      int count = (f != null && f.until <= now && f.count >= maxFailures ? 0 : f == null ? 0 : f.count) + 1;
      return new Fail(count, count >= maxFailures ? now + lockMillis : 0);
    });
  }

  public void success(String username) {
    fails.remove(username);
  }
}
