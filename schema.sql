CREATE TABLE url_info (url_id BIGINT UNSIGNED AUTO_INCREMENT NOT NULL, url MEDIUMTEXT NOT NULL, times_ref_weight FLOAT UNSIGNED DEFAULT 0.0, crawled BOOL DEFAULT 0, indexed BOOL DEFAULT 0, PRIMARY KEY (url_id));
CREATE TABLE keywords (url_id BIGINT UNSIGNED NOT NULL, word TINYTEXT NOT NULL, FOREIGN KEY (url_id) REFERENCES url_info(url_id));
CREATE UNIQUE INDEX url ON url_info (url);
CREATE INDEX crawled ON url_info (crawled);
CREATE INDEX indexed ON url_info (indexed);
