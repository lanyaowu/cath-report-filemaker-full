package jp.example.cathreport.api;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * カテレポート（API の JSON 形式。MongoDB 版と同一）。
 * DB 上は cath_reports（ヘッダ列＋画面別 JSONB）と子テーブル
 * （report_history / report_mace / report_images / report_image_data）に分けて保存する。
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class CathReport {
  public String id;
  @NotBlank public String patientRef;
  /** 入力中 / 確定 */
  public String status;
  /** 照合済 */
  public Boolean verified;
  @Valid @NotNull public ReportHeader header;
  public Map<String, Object> cathRecord;
  public Map<String, Object> cagLvg;
  public Map<String, Object> pci;
  public Map<String, Object> pressureIvus;
  public Map<String, Object> pcps;
  public Map<String, Object> conference;
  /** MACE 1〜5（画面項目をそのまま保持） */
  public List<Map<String, Object>> mace = new ArrayList<>();
  public List<Image> images = new ArrayList<>();
  public Map<String, Object> restudy;
  public List<History> history = new ArrayList<>();
  public String createdAt;
  public String updatedAt;
  /** 楽観ロック用（任意）。送られた場合のみ DB の値と照合し、不一致なら 409 */
  public Long version;

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class Image {
    public String id;
    public String category;
    public String takenAt;
    public String view;
    public String lesion;
    public String title;
    public String description;
    public String fileName;
    public String mimeType;
    /** data:<mime>;base64,... 一覧取得では含めない */
    public String dataUrl;
    public Boolean keyImage;
  }

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class History {
    public String at;
    public String by;
    public String action;
  }
}
