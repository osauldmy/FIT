-- upgrade --
CREATE TABLE IF NOT EXISTS "DataSource" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "url" VARCHAR(1024) NOT NULL,
    "type" VARCHAR(32) NOT NULL,
    "jsonpath" VARCHAR(128) NOT NULL,
    "timeout" DOUBLE PRECISION,
    "data" JSONB NOT NULL
);
COMMENT ON TABLE "DataSource" IS 'The DB entity for DataSource';;
-- downgrade --
DROP TABLE IF EXISTS "DataSource";
