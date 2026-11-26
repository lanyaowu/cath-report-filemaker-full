package jp.example.cathreport.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.CompoundIndex;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

/**
 * カテレポート（collection: cath_reports）。1回のカテ検査＝1ドキュメント。
 * 各画面のデータはサブドキュメントとして埋め込む（画面単位で一括保存・一括取得するため）。
 * サブドキュメントの項目定義は docs/data-model.md と frontend/src/types/model.ts を参照。
 */
@Document("cath_reports")
@CompoundIndex(name = "status_verified", def = "{'status': 1, 'verified': 1}")
@JsonIgnoreProperties(ignoreUnknown = true)
public class CathReport {
  @Id public String id;
  /** Patient.id への参照 */
  @NotBlank @Indexed public String patientRef;
  /** 入力中 / 確定 */
  public String status;
  /** 照合済 */
  public Boolean verified;
  @Valid @NotNull public ReportHeader header;
  /** カテ記録（検査情報・医師・血行動態・検査値・危険因子・予後） */
  public Map<String, Object> cathRecord;
  /** CAG/LVG（アプローチ・カテーテル・セグメント所見・側副血行路・グラフト・LVG） */
  public Map<String, Object> cagLvg;
  /** PCI（基本・病変×5・Device・Bif/CTO・合併症・J-PCI・出血/血栓リスク・AMI） */
  public Map<String, Object> pci;
  /** Pressure Wire ×3 列 / IVUS Lesion ×4 */
  public Map<String, Object> pressureIvus;
  public Map<String, Object> pcps;
  public Map<String, Object> conference;
  /** MACE 1〜5 */
  public List<Map<String, Object>> mace = new ArrayList<>();
  /** 画像（dataUrl を含む） */
  public List<Map<String, Object>> images = new ArrayList<>();
  public Map<String, Object> restudy;
  /** レポート登録履歴: at, by, action */
  public List<Map<String, Object>> history = new ArrayList<>();
  public String createdAt;
  public String updatedAt;
  /** 楽観ロック用。保存のたびに +1。更新時は取得した値を送る（不一致・未指定は 409） */
  public Long version;
}
