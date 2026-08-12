-- ============================================================================
-- Enterprise AI Knowledge Platform
-- SPCS Service Deployment: Container service for REST API
-- ============================================================================

USE ROLE CORTEX_AI_ADMIN;
USE DATABASE CORTEX_AI_PLATFORM;

-- Image repository for the API container
CREATE IMAGE REPOSITORY IF NOT EXISTS CORTEX_AI_PLATFORM.RAW.API_IMAGES;

-- Compute pool for the API service
CREATE COMPUTE POOL IF NOT EXISTS CORTEX_AI_API_POOL
    MIN_NODES = 1
    MAX_NODES = 3
    INSTANCE_FAMILY = CPU_X64_XS
    COMMENT = 'Compute pool for the REST API service';

-- Service specification
CREATE SERVICE IF NOT EXISTS CORTEX_AI_PLATFORM.AGENT.KNOWLEDGE_API_SERVICE
    IN COMPUTE POOL CORTEX_AI_API_POOL
    FROM SPECIFICATION $$
    spec:
      containers:
        - name: api
          image: /cortex_ai_platform/raw/api_images/knowledge-api:latest
          env:
            ENVIRONMENT: prod
            SNOWFLAKE_ACCOUNT: ${SNOWFLAKE_ACCOUNT}
            SNOWFLAKE_DATABASE: CORTEX_AI_PLATFORM
            SNOWFLAKE_ROLE: CORTEX_AI_SERVICE
            SNOWFLAKE_WAREHOUSE: CORTEX_AI_SEARCH_WH
            DISABLE_AUTH: "false"
          resources:
            requests:
              cpu: "0.5"
              memory: 1Gi
            limits:
              cpu: "2"
              memory: 4Gi
          readinessProbe:
            httpGet:
              path: /api/v1/ready
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 10
      endpoints:
        - name: api
          port: 8080
          public: true
    $$
    MIN_INSTANCES = 1
    MAX_INSTANCES = 3
    COMMENT = 'Enterprise AI Knowledge Platform REST API';

-- Grant access to the service endpoint
GRANT USAGE ON SERVICE CORTEX_AI_PLATFORM.AGENT.KNOWLEDGE_API_SERVICE TO ROLE CORTEX_AI_USER;
