-- upgrade --
ALTER TABLE "project" DROP CONSTRAINT "project_pkey";
ALTER TABLE "project" ADD PRIMARY KEY ("uuid");
ALTER TABLE "project" DROP COLUMN "id";
