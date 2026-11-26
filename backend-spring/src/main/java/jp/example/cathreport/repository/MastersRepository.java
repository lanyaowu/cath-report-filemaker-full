package jp.example.cathreport.repository;

import jp.example.cathreport.model.Masters;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface MastersRepository extends MongoRepository<Masters, String> {}
