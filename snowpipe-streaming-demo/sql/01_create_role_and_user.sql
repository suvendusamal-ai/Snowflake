-- Run with ACCOUNTADMIN or another sufficiently privileged role.
USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS STREAMING_ROLE;

-- Replace SUVENDU when using a dedicated service user.
-- If the user already exists, omit CREATE USER and only run ALTER USER.
CREATE USER IF NOT EXISTS SUVENDU
  DEFAULT_ROLE = STREAMING_ROLE
  COMMENT = 'Snowpipe Streaming demo user';

GRANT ROLE STREAMING_ROLE TO USER SUVENDU;

-- Replace the placeholder with the single-line body of keys/rsa_key.pub.
ALTER USER SUVENDU
  SET RSA_PUBLIC_KEY = 'PASTE_PUBLIC_KEY_BODY_HERE';

ALTER USER SUVENDU SET DEFAULT_ROLE = STREAMING_ROLE;
