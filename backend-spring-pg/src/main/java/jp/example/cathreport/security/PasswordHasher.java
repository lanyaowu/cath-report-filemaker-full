package jp.example.cathreport.security;

import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

/**
 * パスワードのハッシュ（PBKDF2-HMAC-SHA256）。
 * 形式 "pbkdf2_sha256$反復回数$salt(Base64)$hash(Base64)" は Node.js 版（tools/auth/hash_password.mjs）と共通。
 */
public final class PasswordHasher {
  public static final int ITERATIONS = 120_000;
  private static final SecureRandom RANDOM = new SecureRandom();

  private PasswordHasher() {}

  public static String hash(String password) {
    byte[] salt = new byte[16];
    RANDOM.nextBytes(salt);
    return hash(password, ITERATIONS, salt);
  }

  public static String hash(String password, int iterations, byte[] salt) {
    byte[] h = pbkdf2(password, salt, iterations, 32);
    Base64.Encoder b = Base64.getEncoder();
    return "pbkdf2_sha256$" + iterations + "$" + b.encodeToString(salt) + "$" + b.encodeToString(h);
  }

  public static boolean verify(String password, String stored) {
    if (password == null || stored == null) return false;
    String[] p = stored.split("\\$");
    if (p.length != 4 || !"pbkdf2_sha256".equals(p[0])) return false;
    try {
      byte[] salt = Base64.getDecoder().decode(p[2]);
      byte[] expected = Base64.getDecoder().decode(p[3]);
      byte[] actual = pbkdf2(password, salt, Integer.parseInt(p[1]), expected.length);
      return MessageDigest.isEqual(expected, actual);
    } catch (IllegalArgumentException e) {
      return false;
    }
  }

  private static byte[] pbkdf2(String password, byte[] salt, int iterations, int bytes) {
    try {
      PBEKeySpec spec = new PBEKeySpec(password.toCharArray(), salt, iterations, bytes * 8);
      return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded();
    } catch (java.security.GeneralSecurityException e) {
      throw new IllegalStateException(e);
    }
  }
}
