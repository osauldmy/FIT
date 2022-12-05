-- upgrade --
ALTER TABLE "project" ADD "name" VARCHAR(64) NOT NULL DEFAULT 'Project';
ALTER TABLE "project" ALTER COLUMN "name" DROP DEFAULT;
ALTER TABLE "project" ADD "description" VARCHAR(512);
-- downgrade --
ALTER TABLE "project" DROP COLUMN "name";
ALTER TABLE "project" DROP COLUMN "description";
