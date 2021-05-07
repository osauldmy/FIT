-- upgrade --
ALTER TABLE "datasource" ADD "name" VARCHAR(64) NOT NULL;
ALTER TABLE "datasource" ADD "cache_expire" INT;
-- downgrade --
ALTER TABLE "datasource" DROP COLUMN "name";
ALTER TABLE "datasource" DROP COLUMN "cache_expire";
