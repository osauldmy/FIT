-- upgrade --
CREATE TABLE IF NOT EXISTS "project" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "uuid" UUID NOT NULL,
    "slug" VARCHAR(128) NOT NULL
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSONB NOT NULL
);
