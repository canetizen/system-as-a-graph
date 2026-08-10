-- Stand-in configuration management database (EXT-IF-01).
--
-- Deliberately not SaaG's schema: it is one plausible shape a customer's
-- configuration management database might have. MSD never sees these table or
-- column names — the queries that read them live in the source configuration,
-- so a real database with entirely different tables needs no code change.

CREATE TABLE project (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(128) NOT NULL UNIQUE
);

CREATE TABLE platform (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    code       VARCHAR(128) NOT NULL,
    UNIQUE KEY platform_of_project (project_id, code),
    FOREIGN KEY (project_id) REFERENCES project (id)
);

CREATE TABLE system_release (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    platform_id  INT NOT NULL,
    release_no   VARCHAR(64) NOT NULL,
    in_service   TINYINT(1) NOT NULL DEFAULT 0,
    UNIQUE KEY release_of_platform (platform_id, release_no),
    FOREIGN KEY (platform_id) REFERENCES platform (id)
);

CREATE TABLE release_component (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    system_release_id INT NOT NULL,
    component_name    VARCHAR(128) NOT NULL,
    component_version VARCHAR(64) NOT NULL,
    repository        VARCHAR(128) NULL,
    FOREIGN KEY (system_release_id) REFERENCES system_release (id)
);
