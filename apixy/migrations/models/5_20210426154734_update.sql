-- upgrade --
ALTER TABLE "project" ADD "merge_strategy" VARCHAR(32) NOT NULL;
-- downgrade --
ALTER TABLE "project" DROP COLUMN "merge_strategy";
