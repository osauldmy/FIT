-- upgrade --
ALTER TABLE "DataSource" RENAME TO "datasource";
ALTER TABLE "Project" RENAME TO "project";
-- downgrade --
ALTER TABLE "project" RENAME TO "Project";
ALTER TABLE "datasource" RENAME TO "DataSource";
