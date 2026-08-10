-- Demo content for the stand-in configuration management database.
-- Mirrors what the earlier JSON fixture described: one project, one platform,
-- two system versions with the newer one in service, and the software units
-- each version is built from.

INSERT INTO project (code) VALUES ('skyline');

INSERT INTO platform (project_id, code)
SELECT id, 'avionics' FROM project WHERE code = 'skyline';

INSERT INTO system_release (platform_id, release_no, in_service)
SELECT p.id, '1.0.0', 1
FROM platform p JOIN project pr ON pr.id = p.project_id
WHERE pr.code = 'skyline' AND p.code = 'avionics';

INSERT INTO system_release (platform_id, release_no, in_service)
SELECT p.id, '0.9.0', 0
FROM platform p JOIN project pr ON pr.id = p.project_id
WHERE pr.code = 'skyline' AND p.code = 'avionics';

-- Effective version: system_repo and nav_app are pinned to a repository,
-- the rest are found by searching the configured repositories in order.
INSERT INTO release_component (system_release_id, component_name, component_version, repository)
SELECT r.id, v.component_name, v.component_version, v.repository
FROM system_release r
JOIN platform p ON p.id = r.platform_id
JOIN project pr ON pr.id = p.project_id
JOIN (
    SELECT 'system_repo' AS component_name, '1.0.0' AS component_version, 'bitbucket-a' AS repository
    UNION ALL SELECT 'nav_app',    '1.2.0', 'bitbucket-a'
    UNION ALL SELECT 'sensor_app', '2.0.1', NULL
    UNION ALL SELECT 'helper_lib', '1.0.0', NULL
) AS v
WHERE pr.code = 'skyline' AND p.code = 'avionics' AND r.release_no = '1.0.0';

-- Superseded version, kept so the effective-version marking has something to
-- be distinct from.
INSERT INTO release_component (system_release_id, component_name, component_version, repository)
SELECT r.id, v.component_name, v.component_version, v.repository
FROM system_release r
JOIN platform p ON p.id = r.platform_id
JOIN project pr ON pr.id = p.project_id
JOIN (
    SELECT 'system_repo' AS component_name, '1.0.0' AS component_version, 'bitbucket-a' AS repository
    UNION ALL SELECT 'nav_app', '1.1.0', 'bitbucket-a'
) AS v
WHERE pr.code = 'skyline' AND p.code = 'avionics' AND r.release_no = '0.9.0';
