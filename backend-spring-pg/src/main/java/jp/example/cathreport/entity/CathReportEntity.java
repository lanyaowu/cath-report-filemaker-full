package jp.example.cathreport.entity;

import jakarta.persistence.*;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

/**
 * カテレポート（table: cath_reports）。
 * ヘッダ・ステータスは列、画面ごとの詳細は JSONB 列、履歴・MACE・画像メタは子テーブル。
 * 画像本体（report_image_data）は ImageDataDao で別に読み書きする。
 */
@Entity
@Table(name = "cath_reports")
public class CathReportEntity {
  @Id public String id;
  /** patients.id（外部キー。関連オブジェクトにはせず ID で保持） */
  public String patientRef;
  public String status;
  public boolean verified;

  @Embedded public HeaderEmb header = new HeaderEmb();

  @JdbcTypeCode(SqlTypes.JSON) public Map<String, Object> cathRecord;
  @JdbcTypeCode(SqlTypes.JSON) public Map<String, Object> cagLvg;
  @JdbcTypeCode(SqlTypes.JSON) public Map<String, Object> pci;
  @JdbcTypeCode(SqlTypes.JSON) public Map<String, Object> pressureIvus;
  @JdbcTypeCode(SqlTypes.JSON) public Map<String, Object> pcps;
  @JdbcTypeCode(SqlTypes.JSON) public Map<String, Object> conference;
  @JdbcTypeCode(SqlTypes.JSON) public Map<String, Object> restudy;

  @ElementCollection
  @CollectionTable(name = "report_history", joinColumns = @JoinColumn(name = "report_id"))
  @OrderColumn(name = "seq")
  public List<HistoryEmb> history = new ArrayList<>();

  @ElementCollection
  @CollectionTable(name = "report_mace", joinColumns = @JoinColumn(name = "report_id"))
  @OrderColumn(name = "seq")
  public List<MaceEmb> mace = new ArrayList<>();

  @ElementCollection
  @CollectionTable(name = "report_images", joinColumns = @JoinColumn(name = "report_id"))
  @OrderColumn(name = "seq")
  public List<ImageEmb> images = new ArrayList<>();

  public Instant createdAt;
  public Instant updatedAt;
  @Version public Long version;

  /** ヘッダ（cath_reports の列） */
  @Embeddable
  public static class HeaderEmb {
    public LocalDate studyDate;
    public String cineNo;
    public String pciNo;
    public String accessionNo;
    public boolean secretaryChecked;
    public boolean summary;
    public boolean submitted;
    public boolean qca;
    public String registrant;
  }

  /** 登録履歴（report_history） */
  @Embeddable
  public static class HistoryEmb {
    public Instant at;
    @Column(name = "by_name") public String by;
    public String action;
  }

  /** MACE（report_mace）。data が画面の全項目、その他は集計用に展開した列 */
  @Embeddable
  public static class MaceEmb {
    public String mace;
    public LocalDate pciDate;
    public LocalDate lastVisit;
    public boolean hasDeath;
    public boolean hasAcs;
    public boolean hasStroke;
    public boolean hasHf;
    public boolean hasBleeding;
    public boolean hasRevasc;
    public boolean hasOther;
    public LocalDate firstEventDate;
    @JdbcTypeCode(SqlTypes.JSON) public Map<String, Object> data;
  }

  /** 画像メタ情報（report_images） */
  @Embeddable
  public static class ImageEmb {
    public String imageId;
    public String category;
    public LocalDate takenAt;
    @Column(name = "view_name") public String view;
    public String lesion;
    public String title;
    public String description;
    public String fileName;
    public String mimeType;
    public boolean keyImage;
  }
}
