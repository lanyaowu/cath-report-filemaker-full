package jp.example.cathreport.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.NotBlank;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

/**
 * 患者（collection: patients）。
 * フィールドはフロントエンドの types/model.ts の Patient と1対1で対応する。
 * 簡潔さのため public フィールド（Jackson / Spring Data の双方がフィールドアクセスで動作）。
 */
@Document("patients")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Patient {
  @Id public String id;
  @NotBlank @Indexed(unique = true, sparse = true) public String patientId;
  @NotBlank public String name;
  @Indexed public String kana;
  public String sex;
  public String birthDate;
  public String bloodType;
  public String rh;
  public String zip;
  public String address;
  public String phone;
  public String mobile;
  /** name, relation, phone */
  public Map<String, Object> emergency;
  /** type, number */
  public Map<String, Object> insurance;
  /** contrast, contrastDetail, drug, drugDetail, latex, iodine, food */
  public Map<String, Object> allergy;
  /** hbs, hcv, hiv, syphilis, mrsa（"-" / "+" / "unknown"） */
  public Map<String, Object> infection;
  public String primaryDoctor;
  public String ward;
  /** hospital, doctor */
  public Map<String, Object> referral;
  public Boolean dnar;
  public String pastHistory;
  public String familyHistory;
  public String medicationNote;
  public String notes;
  /** 病歴総括: admitDate, dischargeDate, doctor, diagnosis, summary */
  public List<Map<String, Object>> admissions = new ArrayList<>();
  public String createdAt;
  public String updatedAt;
  /** 楽観ロック用。保存のたびに +1。更新時は取得した値を送る（不一致・未指定は 409） */
  public Long version;
}
