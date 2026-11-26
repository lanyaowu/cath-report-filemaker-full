package jp.example.cathreport.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.ArrayList;
import java.util.List;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

/** マスタ（collection: masters, _id = "default"） */
@Document("masters")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Masters {
  public static final String DEFAULT_ID = "default";

  @Id @JsonIgnore public String id = DEFAULT_ID;
  public List<String> doctors = new ArrayList<>();
  public List<String> hospitals = new ArrayList<>();
  public List<DeviceMaster> devices = new ArrayList<>();

  @JsonIgnoreProperties(ignoreUnknown = true)
  public static class DeviceMaster {
    public String category;
    public String name;
  }
}
