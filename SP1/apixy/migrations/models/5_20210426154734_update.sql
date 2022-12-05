-- upgrade --
ALTER TABLE "project" ADD "merge_strategy" VARCHAR(32) NOT NULL DEFAULT 'concatenation';
ALTER TABLE "project" ALTER COLUMN "merge_strategy" DROP DEFAULT;
-- downgrade --
ALTER TABLE "project" DROP COLUMN "merge_strategy";
