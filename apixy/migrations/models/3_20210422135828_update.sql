-- upgrade --
ALTER TABLE "project" DROP CONSTRAINT "project_pkey";
ALTER TABLE "project" ADD COLUMN "id" SERIAL NOT NULL PRIMARY KEY;
ALTER TABLE "project" DROP COLUMN "uuid";
