-- upgrade --
CREATE UNIQUE INDEX "uid_project_slug_2d2cec" ON "project" ("slug");
-- downgrade --
DROP INDEX "idx_project_slug_2d2cec";
