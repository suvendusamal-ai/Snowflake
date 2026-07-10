USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE PIPE STREAMING_DEMO.RAW.IOT_EVENTS_STREAMING
COMMENT = 'Named high-performance Snowpipe Streaming pipe for IoT demo'
AS
COPY INTO STREAMING_DEMO.RAW.IOT_EVENTS
    (device_id, event_type, temperature, humidity, payload)
FROM (
    SELECT
        $1:device_id::STRING,
        $1:event_type::STRING,
        $1:temperature::FLOAT,
        $1:humidity::FLOAT,
        $1:payload::VARIANT
    FROM TABLE(DATA_SOURCE(TYPE => 'STREAMING'))
);
