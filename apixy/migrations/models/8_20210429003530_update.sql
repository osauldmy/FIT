-- upgrade --
CREATE TABLE "projects_sources" ("datasource_id" INT NOT NULL REFERENCES "datasource" ("id") ON DELETE CASCADE,"project_id" INT NOT NULL REFERENCES "project" ("id") ON DELETE CASCADE);
-- downgrade --
DROP TABLE IF EXISTS "projects_sources";
