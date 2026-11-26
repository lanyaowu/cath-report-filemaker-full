package jp.example.cathreport.api;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.NotBlank;

/** レポートヘッダ（施行日・Cine No・PCI No・各種チェック） */
@JsonIgnoreProperties(ignoreUnknown = true)
public class ReportHeader {
  @NotBlank public String studyDate;
  public String cineNo;
  public String pciNo;
  public String accessionNo;
  public Boolean secretaryChecked;
  public Boolean summary;
  public Boolean submitted;
  public Boolean qca;
  public String registrant;
}
