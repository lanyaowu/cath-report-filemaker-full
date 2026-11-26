package jp.example.cathreport.api;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.ArrayList;
import java.util.List;

/** マスタ（API 形式）。DB 上は master_items に kind 別で保存 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class Masters {
  public List<String> doctors = new ArrayList<>();
  public List<String> hospitals = new ArrayList<>();
  public List<DeviceMaster> devices = new ArrayList<>();

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class DeviceMaster {
    public String category;
    public String name;

    public DeviceMaster() {}

    public DeviceMaster(String category, String name) {
      this.category = category;
      this.name = name;
    }
  }
}
