-- upgrade --
ALTER TABLE "project" RENAME TO "Project";
-- downgrade --
ALTER TABLE "Project" RENAME TO "project";
