-- upgrade --
ALTER TABLE "DataSource" RENAME TO "datasource";
ALTER SEQUENCE "DataSource_id_seq" RENAME TO "datasource_id_seq";
ALTER TABLE "Project" RENAME TO "project";
-- downgrade --
ALTER TABLE "project" RENAME TO "Project";
ALTER TABLE "datasource" RENAME TO "DataSource";
ALTER SEQUENCE "datasource_id_seq" RENAME TO "DataSource_id_seq";
