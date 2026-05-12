# AWS Interview Questions for Dean Peng

Based on the candidate's CV: ~6 years DevOps experience, AWS SAP certified, CKA certified, strong EKS/Kubernetes background, Terraform, GitOps (ArgoCD), monitoring stacks, Istio service mesh, and cost optimization experience.

---

## Question 1: EKS Multi-Cluster Architecture

**Q:** In your Samsung Health project, you set up Kubernetes multi-cluster environments via TFE. What factors drove the decision to use multiple EKS clusters instead of a single cluster? How did you handle cross-cluster service communication and traffic routing?

**A (Expected points):**
- Reasons for multi-cluster: environment isolation (dev/staging/prod), blast radius reduction, regional availability, team autonomy, compliance boundaries
- Traffic routing options: Route 53 weighted/latency-based routing, AWS Global Accelerator, or service mesh federation
- Cross-cluster communication: Istio multi-cluster mesh, AWS PrivateLink, or VPC peering
- Terraform Enterprise (TFE) for consistent cluster provisioning with workspaces per cluster
- Challenges: state management, configuration drift, keeping clusters in sync

---

## Question 2: Karpenter vs Cluster Autoscaler

**Q:** You used Karpenter for node autoscaling and achieved a 20% cost reduction. Explain how Karpenter differs from the traditional Cluster Autoscaler, and walk through how you configured NodePools with Spot instances while handling interruptions.

**A (Expected points):**
- Cluster Autoscaler scales node groups; Karpenter provisions individual nodes directly based on pod requirements (right-sizing)
- Karpenter eliminates the need for pre-defined node groups, choosing optimal instance types dynamically
- NodePool configuration: defining instance families, capacity types (spot/on-demand), architecture constraints
- EC2NodeClass: AMI selection, subnet/security group configuration, userData
- Spot interruption handling: SQS interruption queue, Karpenter watches for ITN (Instance Termination Notifications) and proactively cordons/drains nodes
- Lambda function to distribute Karpenter events across clusters
- Consolidation policies to bin-pack workloads and terminate underutilized nodes

---

## Question 3: GitOps with ArgoCD on EKS

**Q:** You built a GitLab CI + ArgoCD GitOps pipeline. Explain the separation of concerns between GitLab CI and ArgoCD in your workflow. How did you handle multi-environment deployments (dev/staging/prod) and rollbacks?

**A (Expected points):**
- GitLab CI handles: code build, unit tests, container image build and push to ECR, update image tag in Git manifests
- ArgoCD handles: continuous reconciliation of cluster state with Git, deployment to EKS, health checks
- Multi-environment strategy: Kustomize overlays per environment or Helm values files per environment, separate Git branches or directories
- Rollback: revert the Git commit (ArgoCD syncs automatically), or use ArgoCD's built-in rollback to a previous sync revision
- App-of-apps pattern for managing multiple services
- Sync policies: auto-sync vs manual sync for production, sync waves for ordering

---

## Question 4: Istio Service Mesh on EKS

**Q:** You configured Istio authorization policies and used Kiali for observability. Describe how Istio's sidecar injection works on EKS, and give an example of an authorization policy you implemented to secure microservice communication.

**A (Expected points):**
- Sidecar injection: Istio mutating webhook intercepts pod creation, injects Envoy proxy container alongside the application container
- Namespace labeling (`istio-injection=enabled`) to enable automatic injection
- Authorization policy example:
  ```yaml
  apiVersion: security.istio.io/v1
  kind: AuthorizationPolicy
  metadata:
    name: allow-frontend-to-backend
    namespace: backend
  spec:
    selector:
      matchLabels:
        app: backend-service
    rules:
    - from:
      - source:
          principals: ["cluster.local/ns/frontend/sa/frontend-sa"]
      to:
      - operation:
          methods: ["GET", "POST"]
          paths: ["/api/*"]
  ```
- mTLS enforcement between services (PeerAuthentication policy)
- Kiali: visualizes service topology, traffic flow, error rates, latency between services
- Jaeger integration for distributed tracing

---

## Question 5: ECR Cross-Account Replication

**Q:** You mentioned cross-account ECR replication. Why is this needed in a multi-account AWS setup, and how did you configure it? What IAM considerations are involved?

**A (Expected points):**
- Why: organizations use separate AWS accounts for dev/staging/prod; images built in CI (dev account) need to be available in prod account
- ECR replication configuration: replication rules in the source registry specifying destination regions and accounts
- Alternative: ECR repository policies granting cross-account pull access
- IAM considerations:
  - Source account: replication service role needs `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer`
  - Destination account: repository policy allowing the source account to replicate
  - EKS nodes in destination account need `ecr:GetAuthorizationToken` and `ecr:BatchGetImage`
- Image immutability tags to prevent overwrites
- Lifecycle policies to manage image retention and cost

---

## Question 6: Terraform State Management and Multi-Environment

**Q:** With your Terraform experience across multiple projects, how do you structure Terraform code for managing multiple EKS clusters across environments? How do you handle state locking and prevent drift?

**A (Expected points):**
- Remote state backend: S3 bucket + DynamoDB table for state locking
- Workspace strategy: TFE workspaces per environment/cluster, or directory-based separation
- Module structure: reusable modules for VPC, EKS, IAM roles; environment-specific tfvars
- State locking: DynamoDB prevents concurrent modifications
- Drift detection: `terraform plan` in CI pipeline on schedule, TFE drift detection feature
- Sensitive data: use `sensitive` flag, store secrets in AWS Secrets Manager, reference via data sources
- Import existing resources with `terraform import` when adopting IaC
- Blast radius: separate state files per component (networking, compute, platform) to limit impact of changes

---

## Question 7: EKS Monitoring Stack Design

**Q:** You built monitoring with VictoriaMetrics + Grafana + Alertmanager and collected multi-cluster metrics. How did you architect the monitoring to handle multiple clusters, and how does VictoriaMetrics compare to running Prometheus directly?

**A (Expected points):**
- Architecture: remote-write from Prometheus/vmagent in each cluster to a centralized VictoriaMetrics cluster
- VictoriaMetrics advantages over Prometheus: better compression, horizontal scalability (vmcluster), long-term retention, lower resource usage, PromQL-compatible
- Multi-cluster: external labels to distinguish clusters, centralized Grafana with datasource per cluster or single VictoriaMetrics datasource
- Alertmanager: centralized or per-cluster, routing alerts by severity/team/cluster
- Loki for logs: Promtail/Grafana Agent on each node ships logs to centralized Loki
- Key metrics to monitor on EKS: node resource usage, pod restarts, HPA scaling events, API server latency, etcd health
- Grafana dashboards: cluster overview, namespace resource usage, Karpenter node provisioning

---

## Question 8: VPC Design for EKS

**Q:** When you plan AWS VPC infrastructure for EKS, what are the key networking considerations? How do you size subnets, and what's the difference between using public vs private subnets for EKS worker nodes?

**A (Expected points):**
- EKS requires subnets in at least 2 AZs
- Private subnets for worker nodes (security best practice), public subnets only for load balancers
- Subnet sizing: each pod consumes an IP (with VPC CNI), so subnets need large CIDR blocks (e.g., /19 or /18)
- VPC CNI considerations: secondary CIDR ranges or prefix delegation to avoid IP exhaustion
- NAT Gateway in public subnet for outbound internet access from private nodes
- Security groups: cluster security group, node security group, pod security groups (optional)
- VPC endpoints for ECR, S3, STS, CloudWatch to reduce NAT costs and improve security
- Tagging requirements: `kubernetes.io/cluster/<name>` tags on subnets for EKS auto-discovery

---

## Question 9: AWS Lambda for Operational Automation

**Q:** You developed Lambda functions for deployment and for distributing Karpenter events. Walk through how you would design a Lambda function that listens to an SQS queue for Spot interruption notices and takes action on your EKS cluster.

**A (Expected points):**
- Architecture: EventBridge rule catches EC2 Spot Interruption Warning → SQS queue → Lambda trigger
- Lambda function logic:
  1. Parse the event to get instance ID
  2. Use Kubernetes API (via boto3 for EKS auth + kubernetes Python client) to identify the node
  3. Cordon the node (`kubectl cordon`)
  4. Drain the node (evict pods gracefully)
- IAM role for Lambda: `eks:DescribeCluster` for auth, SQS permissions, EC2 describe permissions
- EKS auth: Lambda assumes a role mapped in aws-auth ConfigMap or EKS access entries
- Timeout considerations: set Lambda timeout to handle drain gracefully (Spot gives 2-minute warning)
- Error handling: DLQ on SQS for failed processing, CloudWatch alarms on Lambda errors
- Alternative: Karpenter natively handles this via its interruption controller with SQS

---

## Question 10: Sealed Secrets and Secret Management on EKS

**Q:** You used Sealed Secrets in your advertising platform project. Why use Sealed Secrets instead of storing Kubernetes secrets directly in Git? What are the alternatives, and when would you choose each?

**A (Expected points):**
- Problem: Kubernetes Secrets are base64-encoded (not encrypted), unsafe to commit to Git
- Sealed Secrets: encrypts secrets client-side with a public key; only the cluster's controller can decrypt with the private key
- Workflow: `kubeseal` CLI encrypts → SealedSecret resource committed to Git → controller decrypts in-cluster → creates regular Secret
- Fits GitOps perfectly: encrypted secrets live alongside manifests in Git
- Alternatives:
  - **AWS Secrets Manager + External Secrets Operator**: secrets stored in AWS, synced to K8s; better for rotation and cross-service access
  - **SOPS (Mozilla)**: encrypts specific values in YAML files using KMS; works with ArgoCD via plugins
  - **HashiCorp Vault**: full-featured secrets management with dynamic secrets, leasing, and audit; heavier to operate
- When to choose:
  - Sealed Secrets: simple GitOps setups, small teams, secrets don't need rotation
  - External Secrets + AWS SM: enterprise environments, secrets shared across services, need rotation
  - Vault: complex multi-cloud environments, dynamic database credentials, strict compliance requirements
