-- upgrade --
CREATE TABLE IF NOT EXISTS "fetchlogmodel" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "status" BOOL NOT NULL,
    "nanoseconds" BIGINT NOT NULL,
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "datasource_id_id" INT NOT NULL REFERENCES "datasource" ("id") ON DELETE CASCADE
);
-- downgrade --
DROP TABLE IF EXISTS "fetchlogmodel";
