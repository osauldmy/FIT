-- upgrade --
CREATE TABLE IF NOT EXISTS "fetchlogmodel" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "status" SMALLINT NOT NULL,
    "nanoseconds" BIGINT NOT NULL,
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "datasource_id" INT NOT NULL REFERENCES "datasource" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "fetchlogmodel"."status" IS 'success: 1\ntimeout: 2\nerror: 3';
-- downgrade --
DROP TABLE IF EXISTS "fetchlogmodel";
