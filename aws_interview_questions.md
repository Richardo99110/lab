# AWS Technical Interview Questions

## Question 1: EC2 Instance Types and Use Cases

**Q:** What are the different EC2 instance families and when would you choose each one?

**A:** 
- **General Purpose (e.g., t3, m5):** Balanced compute, memory, and networking. Good for web servers, small databases, and development environments.
- **Compute Optimized (e.g., c5):** High performance processors. Ideal for batch processing, gaming servers, and scientific modeling.
- **Memory Optimized (e.g., r5, x1):** Large memory for in-memory databases, real-time big data analytics, and caching.
- **Storage Optimized (e.g., i3, d2):** High sequential read/write access. Used for data warehousing, Hadoop, and log processing.
- **Accelerated Computing (e.g., p4, g5):** Hardware accelerators (GPUs). Used for machine learning training and graphics-intensive workloads.

---

## Question 2: VPC Architecture

**Q:** Explain the difference between a public subnet and a private subnet in a VPC. How do you make a subnet public?

**A:**
A **private subnet** does not have direct internet access. Instances cannot receive inbound traffic from the internet and cannot initiate outbound connections to the internet.

A **public subnet** has internet access. To make a subnet public:
1. Attach an **Internet Gateway (IGW)** to the VPC
2. Create a **route table** with a route to the IGW (0.0.0.0/0 → IGW)
3. Associate that route table with the subnet
4. Ensure instances have a **public IP address** (or Elastic IP)

For private subnets needing outbound internet access, use a **NAT Gateway** or **NAT instance** in a public subnet.

---

## Question 3: Lambda and Cold Starts

**Q:** What is a Lambda cold start and how can you mitigate its impact?

**A:**
A **cold start** occurs when Lambda has no existing container ready to serve a request. AWS must provision a new execution environment, load the function code, and run initialization code before handling the actual request. This adds latency (typically 100ms to several seconds).

**Mitigation strategies:**
- Use **provisioned concurrency** to keep containers warm and ready
- Keep the deployment package small to reduce load time
- Minimize initialization code in the handler
- Use **Lambda SnapStart** (for Java) which caches initialized state
- Implement a warm-up mechanism (scheduled pings to keep functions active)
- Choose runtimes with faster initialization (e.g., Python over Java)

---

## Question 4: S3 Consistency and Storage Classes

**Q:** What are the S3 storage classes and how do you choose between them? Also, explain S3 consistency model.

**A:**

**Storage Classes (cost to performance, highest to lowest):**
- **S3 Standard:** Frequent access, 99.99% availability, default choice
- **S3 Intelligent-Tiering:** Automatic optimization between access patterns, small monitoring fee
- **S3 Standard-IA (Infrequent Access):** Long-lived, infrequently accessed data, retrieval fees apply
- **S3 One Zone-IA:** Non-critical, infrequently accessed data (only one AZ)
- **S3 Glacier Instant Retrieval:** Archive data with instant access (milliseconds)
- **S3 Glacier Flexible Retrieval:** Archive data, retrieval takes minutes to hours
- **S3 Glacier Deep Archive:** Long-term archive, retrieval takes 12+ hours

**Consistency Model:**
Since December 2020, S3 provides **strong read-after-write consistency** for all objects. After a successful write of a new object or overwrite of an existing object, any subsequent read request immediately returns the latest version.

---

## Question 5: IAM Best Practices and Least Privilege

**Q:** Your application running on EC2 needs to read from S3 and write to DynamoDB. How would you implement this securely?

**A:**

1. **Never use IAM user credentials on EC2.** Instead, use an **IAM Role** attached to the EC2 instance profile.

2. **Apply least privilege principle.** Create a policy with only the required permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:region:account:table/my-table"
    }
  ]
}
```

3. **Best practices:**
   - Specify exact resource ARNs, not `*`
   - Grant only the actions needed (Get vs List vs Put)
   - Use **permissions boundaries** for additional control
   - Enable **CloudTrail** to audit API calls
   - Rotate credentials automatically (handled by IAM roles)
   - Use **conditions** in policies (e.g., restrict to specific VPC or IP range)


---

## Question 6: High Availability and Multi-AZ Architectures

**Q:** How would you design a highly available web application on AWS? Walk through the key components.

**A:**

A highly available architecture typically includes:

1. **Multi-AZ deployment:** Distribute resources across at least 2 Availability Zones
2. **Elastic Load Balancer (ALB):** Distributes traffic across instances in multiple AZs, performs health checks, and routes away from unhealthy targets
3. **Auto Scaling Group:** Automatically adds/removes EC2 instances based on demand, replaces unhealthy instances
4. **RDS Multi-AZ:** Primary database with synchronous standby replica in another AZ, automatic failover
5. **Route 53:** DNS with health checks and failover routing policies
6. **ElastiCache:** In-memory caching layer (Redis/Memcached) to reduce database load

**Key design principles:**
- No single point of failure
- Stateless application tier (store session data in ElastiCache or DynamoDB)
- Decouple components using SQS or EventBridge
- Use CloudFront for static content and reduced latency
- Implement circuit breakers and retries with exponential backoff

---

## Question 7: CloudFormation vs Terraform

**Q:** Compare CloudFormation and Terraform. When would you choose one over the other?

**A:**

| Aspect | CloudFormation | Terraform |
|--------|---------------|-----------|
| Provider | AWS-native | Multi-cloud (AWS, Azure, GCP, etc.) |
| Language | JSON/YAML | HCL (HashiCorp Configuration Language) |
| State | Managed by AWS automatically | State file must be managed (e.g., S3 backend) |
| Drift detection | Built-in | `terraform plan` shows drift |
| Rollback | Automatic on failure | Manual (no built-in rollback) |
| Modularity | Nested stacks, modules via CDK | Modules with versioning |

**Choose CloudFormation when:**
- You are AWS-only and want tight integration (StackSets, Service Catalog)
- You want AWS-managed state with no extra setup
- You need automatic rollback on deployment failures

**Choose Terraform when:**
- You work across multiple cloud providers
- You need a more expressive language (loops, conditionals are cleaner in HCL)
- You want a large ecosystem of community modules and providers
- Your team prefers plan/apply workflow with explicit state management

---

## Question 8: SQS vs SNS vs EventBridge

**Q:** Explain the differences between SQS, SNS, and EventBridge. Give a use case for each.

**A:**

**SQS (Simple Queue Service):**
- Point-to-point message queue
- Messages are pulled by consumers
- Guarantees at-least-once delivery
- Supports FIFO (exactly-once, ordered) and Standard (best-effort ordering)
- **Use case:** Decoupling a web tier from a worker tier. Orders placed on a website are queued and processed asynchronously by backend workers.

**SNS (Simple Notification Service):**
- Pub/sub messaging (fan-out)
- Messages are pushed to multiple subscribers simultaneously
- Subscribers can be Lambda, SQS, HTTP endpoints, email, SMS
- **Use case:** An image upload triggers notifications to multiple services: one resizes the image, another updates a database, another sends a confirmation email.

**EventBridge:**
- Serverless event bus with content-based filtering
- Schema registry and discovery
- Supports scheduled events (cron)
- Integrates with SaaS providers (Zendesk, Datadog, etc.)
- **Use case:** Route events from multiple microservices based on event content. E.g., route "order.placed" events to fulfillment service and "order.cancelled" events to refund service using rules.

**Key distinction:** Use SQS for buffering/decoupling, SNS for fan-out, and EventBridge for complex event routing with filtering rules.

---

## Question 9: DynamoDB Design Patterns

**Q:** How do you design a DynamoDB table for an e-commerce application that needs to query orders by customer and by date range?

**A:**

**Table design:**
- **Partition Key (PK):** `CUSTOMER#<customer_id>`
- **Sort Key (SK):** `ORDER#<timestamp>#<order_id>`

This allows:
- Get all orders for a customer: Query where PK = `CUSTOMER#123`
- Get orders in a date range: Query where PK = `CUSTOMER#123` and SK BETWEEN `ORDER#2024-01-01` and `ORDER#2024-12-31`

**For additional access patterns, use GSIs:**
- **GSI1:** PK = `ORDER#<order_id>`, SK = `CUSTOMER#<customer_id>` (lookup order by ID)
- **GSI2:** PK = `STATUS#<status>`, SK = `<timestamp>` (find all pending orders)

**Best practices:**
- Use **single-table design** to reduce the number of tables and enable transactional operations
- Choose partition keys with high cardinality to avoid hot partitions
- Use **sparse indexes** (GSI only contains items with the indexed attribute)
- Set appropriate **RCU/WCU** or use on-demand capacity mode
- Enable **DynamoDB Streams** for change data capture and event-driven processing
- Use **TTL** to automatically expire old data

---

## Question 10: Monitoring and Troubleshooting

**Q:** Your application is experiencing intermittent 5xx errors. Walk through how you would diagnose and resolve this on AWS.

**A:**

**Step 1: Identify the scope**
- Check **CloudWatch Metrics** for ALB: HTTPCode_Target_5XX_Count, TargetResponseTime, HealthyHostCount
- Check **CloudWatch Alarms** for any triggered alerts
- Look at the time correlation — did a deployment happen? Traffic spike?

**Step 2: Drill into logs**
- Enable **ALB access logs** to see which targets are returning 5xx
- Check **CloudWatch Logs** for application error logs
- Use **CloudWatch Logs Insights** to query for error patterns:
  ```
  fields @timestamp, @message
  | filter @message like /ERROR|Exception/
  | sort @timestamp desc
  | limit 50
  ```

**Step 3: Trace the request path**
- Use **AWS X-Ray** to trace individual requests end-to-end
- Identify which downstream service (database, external API, Lambda) is causing failures

**Step 4: Common root causes and fixes**
- **Target health check failures:** Instances failing health checks and being deregistered. Fix: adjust health check thresholds or fix the application crash.
- **Resource exhaustion:** CPU/memory maxed out. Fix: scale up instance size or scale out with Auto Scaling.
- **Database connection limits:** Too many connections. Fix: use connection pooling (RDS Proxy) or increase max connections.
- **Timeout issues:** Downstream service too slow. Fix: increase timeout, add caching, or implement circuit breaker pattern.
- **Deployment issues:** New code introduced a bug. Fix: roll back using CodeDeploy or update the Auto Scaling launch template.

**Step 5: Prevent recurrence**
- Set up CloudWatch Alarms on 5xx rate
- Implement structured logging and dashboards
- Use canary deployments to catch issues before full rollout
