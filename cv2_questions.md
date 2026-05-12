# AWS Interview Questions for Jingda Chen

Based on the candidate's CV: ~3 years software engineering experience, Python backend (FastAPI/Django), AWS Lambda + SAM, DynamoDB, Amazon Bedrock, Kafka, Docker, CI/CD with GitHub Actions, monitoring with Prometheus/Grafana. MSc in Advanced Computing from King's College London.

---

## Question 1: AWS Lambda and SAM Deployment

**Q:** In your AI-Powered Ticket System, you used AWS SAM for deploying Lambda functions. Walk through the SAM template structure for a FastAPI application on Lambda. How does the request reach your FastAPI code, and what are the cold start implications?

**A (Expected points):**
- SAM template defines: `AWS::Serverless::Function` with an API event source
- Lambda Web Adapter or Mangum library to translate API Gateway events into ASGI requests for FastAPI
- Template structure: Globals, Resources (function, API, DynamoDB table), Outputs
- `sam build` compiles dependencies, `sam deploy --guided` deploys via CloudFormation
- Cold starts: FastAPI initialization + model loading adds latency on first invocation
- Mitigation: provisioned concurrency, smaller package size, lazy loading of heavy dependencies
- Layers for shared dependencies across multiple functions

---

## Question 2: DynamoDB Table Design for the Ticket System

**Q:** You built a DynamoDB pipeline with role-based access for your ticket system. How did you design the table schema to support querying tickets by status, by department, and by creation date? How did you implement role-based access?

**A (Expected points):**
- Single-table design with composite keys:
  - PK: `DEPT#<department>`, SK: `TICKET#<timestamp>#<ticket_id>`
  - Allows querying all tickets for a department sorted by time
- GSI for status queries: PK = `STATUS#<status>`, SK = `<timestamp>`
- Role-based access options:
  - IAM policies with condition keys restricting access to specific partition key prefixes
  - Fine-grained access control using IAM policy conditions (`dynamodb:LeadingKeys`)
  - Application-level RBAC: validate user role in Lambda before querying
- DynamoDB Streams for real-time cross-departmental notifications
- TTL for auto-expiring resolved tickets

---

## Question 3: Amazon Bedrock Integration

**Q:** You integrated Amazon Bedrock to parse natural language into structured JSON for ticket classification. Explain how you invoke Bedrock from Lambda, how you handle prompt engineering for reliable JSON output, and what error handling you implemented.

**A (Expected points):**
- Bedrock invocation: `boto3.client('bedrock-runtime').invoke_model()` with model ID and request body
- Prompt engineering for structured output:
  - System prompt defining the JSON schema expected
  - Few-shot examples in the prompt
  - Explicit instructions to return only valid JSON
- Parsing and validation: `json.loads()` on the response, validate against expected schema (e.g., Pydantic model)
- Error handling:
  - Retry with exponential backoff for throttling (ThrottlingException)
  - Fallback classification if LLM returns invalid JSON
  - Timeout handling (Bedrock can be slow for large prompts)
- IAM: Lambda role needs `bedrock:InvokeModel` permission for the specific model
- Cost considerations: token-based pricing, prompt caching for repeated patterns

---

## Question 4: Kafka for Asynchronous Processing

**Q:** You used Kafka to decouple order updates from reporting workflows. If you were to implement this pattern on AWS, what managed service would you use and how would you architect it with Lambda consumers?

**A (Expected points):**
- AWS managed options: Amazon MSK (Managed Streaming for Apache Kafka) or Amazon MSK Serverless
- Alternative: Amazon Kinesis Data Streams for simpler use cases
- Lambda as Kafka consumer: Event Source Mapping connects MSK topic to Lambda
- Architecture:
  - Order service produces to `order-events` topic
  - Lambda consumer processes events for reporting/analytics
  - Separate consumer group for each downstream concern
- Considerations:
  - Batch size and batch window configuration for Lambda
  - Error handling: DLQ for failed records, bisect on function error
  - VPC networking: MSK runs in VPC, Lambda needs VPC access
  - Idempotency: consumer must handle duplicate deliveries
- Comparison to SQS: Kafka provides ordering within partitions, replay capability, and multiple consumer groups

---

## Question 5: CI/CD with GitHub Actions for Multi-Server Deployment

**Q:** You reduced deployment time from 1 hour to 10 minutes using Docker and GitHub Actions across 30+ branch servers. How would you adapt this pipeline to deploy Lambda functions using SAM, including staging and production environments?

**A (Expected points):**
- Pipeline stages: build → test → deploy-staging → integration-test → deploy-prod
- SAM-specific steps:
  ```yaml
  - run: sam build
  - run: sam deploy --stack-name app-staging --parameter-overrides Environment=staging --no-confirm-changeset
  ```
- Environment separation: different SAM parameter files per environment, separate AWS accounts
- GitHub Actions features:
  - Environment protection rules for production (require approval)
  - OIDC for AWS authentication (no long-lived credentials)
  - Reusable workflows for consistency
- Rollback strategy: CloudFormation automatic rollback on failure, or deploy previous known-good artifact
- Testing: run integration tests against staging API endpoint before promoting to prod
- Secrets management: GitHub Secrets for sensitive values, or reference AWS Secrets Manager

---

## Question 6: API Gateway + Lambda Performance and Idempotency

**Q:** You designed idempotent REST APIs using conditional SQL updates. How would you implement idempotency for a Lambda-backed API Gateway endpoint that writes to DynamoDB, ensuring no duplicate processing even with retries?

**A (Expected points):**
- Idempotency key: client sends a unique request ID in header (e.g., `X-Idempotency-Key`)
- DynamoDB conditional writes: `PutItem` with `ConditionExpression: "attribute_not_exists(idempotency_key)"`
- Pattern:
  1. Check if idempotency key exists in a DynamoDB table
  2. If exists, return the cached response
  3. If not, process the request, store result with the key and a TTL
- DynamoDB TTL to auto-expire old idempotency records
- Alternative: AWS Lambda Powertools `@idempotent` decorator handles this pattern automatically
- API Gateway level: enable request deduplication with caching
- Edge cases: handle partial failures (write succeeded but response didn't reach client)

---

## Question 7: Serverless Security and IAM

**Q:** For your serverless ticket system, how did you configure IAM roles following least privilege? What's the difference between the Lambda execution role and resource-based policies on the function?

**A (Expected points):**
- Lambda execution role (identity-based): defines what the Lambda function CAN DO
  - `dynamodb:PutItem`, `dynamodb:Query` on specific table ARN
  - `bedrock:InvokeModel` on specific model ARN
  - `logs:CreateLogGroup`, `logs:PutLogEvents` for CloudWatch
- Resource-based policy: defines WHO can invoke the Lambda
  - API Gateway permission to invoke the function
  - `lambda:InvokeFunction` granted to the API Gateway service principal
- Least privilege practices:
  - Scope to specific resource ARNs, not `*`
  - Separate roles per function if they have different access needs
  - Use SAM `Policies` property with predefined policy templates (e.g., `DynamoDBCrudPolicy`)
- Additional security: VPC placement if accessing private resources, environment variable encryption with KMS

---

## Question 8: Monitoring Serverless Applications

**Q:** You built Prometheus + Grafana monitoring for your restaurant system. For a serverless AWS application (API Gateway + Lambda + DynamoDB), what's different about monitoring? What metrics and tools would you use?

**A (Expected points):**
- Key difference: no servers to install Prometheus on; rely on CloudWatch as the primary metrics source
- Key metrics:
  - API Gateway: 4XX/5XX error rates, latency (p50, p90, p99), request count
  - Lambda: duration, errors, throttles, concurrent executions, cold start frequency (via INIT_START in logs)
  - DynamoDB: consumed RCU/WCU, throttled requests, latency
- Tools:
  - CloudWatch Metrics + Alarms for operational alerts
  - CloudWatch Logs Insights for querying Lambda logs
  - X-Ray for distributed tracing across API GW → Lambda → DynamoDB
  - Lambda Powertools for structured logging and custom metrics
- Grafana integration: CloudWatch datasource plugin to visualize in Grafana
- Custom metrics: use CloudWatch EMF (Embedded Metric Format) from Lambda for business metrics
- Alerting: SNS topics for alarm notifications, or PagerDuty/Slack integration

---

## Question 9: DynamoDB Streams and Event-Driven Architecture

**Q:** You mentioned real-time cross-departmental management in your ticket system. How would you use DynamoDB Streams with Lambda to trigger notifications or workflows when a ticket status changes?

**A (Expected points):**
- DynamoDB Streams: captures item-level changes (INSERT, MODIFY, REMOVE) in order
- Lambda trigger: Event Source Mapping connects stream to a Lambda function
- Filter pattern: only trigger on MODIFY events where `status` field changed
  ```json
  {"eventName": ["MODIFY"], "dynamodb": {"NewImage": {"status": {"S": [{"anything-but": ["OPEN"]}]}}}}
  ```
- Lambda logic:
  - Compare OldImage vs NewImage to detect status change
  - Route notification: SNS for email/SMS, or SES for email, or push to WebSocket API
- Ordering: stream records are ordered per partition key; Lambda processes in order within a shard
- Error handling: bisect batch on error, maximum retry attempts, on-failure destination (SQS DLQ)
- Fan-out pattern: stream → Lambda → EventBridge → multiple targets (notification, audit log, analytics)

---

## Question 10: Cost Optimization for Serverless

**Q:** Your ticket system is fully serverless (Lambda + DynamoDB + Bedrock). How would you estimate and optimize costs as the system scales from 100 to 10,000 tickets per day? What are the biggest cost drivers?

**A (Expected points):**
- Cost drivers ranked:
  1. **Bedrock (LLM invocations):** token-based pricing, likely the largest cost; optimize prompt length, cache common classifications
  2. **Lambda:** charged per invocation + duration × memory; optimize memory allocation (use Power Tuning), reduce execution time
  3. **DynamoDB:** on-demand pricing per read/write request unit; or provisioned with auto-scaling for predictable workloads
  4. **API Gateway:** per-request pricing; consider HTTP API (cheaper) vs REST API
- Optimization strategies:
  - Cache Bedrock responses for similar tickets (DynamoDB or ElastiCache)
  - Batch similar requests if latency allows
  - DynamoDB: use on-demand for unpredictable traffic, switch to provisioned + auto-scaling at scale
  - Lambda: right-size memory (AWS Lambda Power Tuning tool), use ARM64 (Graviton) for 20% cost savings
  - API Gateway: enable caching for repeated GET requests
- Monitoring costs: AWS Cost Explorer, set up billing alarms, tag resources for cost allocation
- At 10K tickets/day: evaluate whether Bedrock cost justifies the automation vs a simpler rule-based classifier for common categories
