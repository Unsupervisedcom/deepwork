# Analyze Cloud Spend

## Objective

Analyze cloud infrastructure costs, identify waste and optimization opportunities, and produce a prioritized list of recommendations with estimated savings. The analysis should help the user understand where money is going, what is being wasted, and what to do about it.

## Task

Gather cost data from available cloud providers, break it down by service and environment, identify idle or oversized resources, and produce actionable savings recommendations.

### Process

#### 1. Read Context and Determine Cloud Provider

Read `context.md` to determine:
- Which cloud CLIs are available (aws, gcloud, az, doctl)
- Which cloud provider(s) the project uses
- Whether Kubernetes is involved (k8s resources may have separate cost implications)
- Whether Terraform or other IaC tools are used (can reveal provisioned resources)

If no cloud CLI is detected in `context.md`, use `AskUserQuestion`:
> No cloud CLI was detected. How would you like to provide cost data?
> 1. I can provide recent billing data or export a CSV
> 2. I have access to a cost management dashboard — I can share screenshots
> 3. I can install the cloud CLI and authenticate now
> 4. Skip cost analysis — I do not have cloud infrastructure

If the user chooses option 1 or 2, work with whatever data they provide. If option 4, produce a minimal report noting that cloud cost analysis is not applicable.

#### 2. Gather Cost Data

Based on the available cloud provider, gather cost and usage data. Use the most appropriate tool for each provider.

**AWS:**
```bash
# Monthly cost breakdown by service (last 3 months)
aws ce get-cost-and-usage \
  --time-period Start=<3-months-ago>,End=<today> \
  --granularity MONTHLY \
  --metrics "BlendedCost" "UnblendedCost" "UsageQuantity" \
  --group-by Type=DIMENSION,Key=SERVICE

# Cost by linked account (if multi-account)
aws ce get-cost-and-usage \
  --time-period Start=<1-month-ago>,End=<today> \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --group-by Type=DIMENSION,Key=LINKED_ACCOUNT

# Cost by tag (if environment tags are used)
aws ce get-cost-and-usage \
  --time-period Start=<1-month-ago>,End=<today> \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --group-by Type=TAG,Key=Environment

# Reserved instance utilization
aws ce get-reservation-utilization \
  --time-period Start=<1-month-ago>,End=<today>

# Savings Plans utilization
aws ce get-savings-plans-utilization \
  --time-period Start=<1-month-ago>,End=<today>
```

**GCP:**
```bash
# List billing accounts
gcloud billing accounts list

# Export billing data (if BigQuery export is configured)
# Check for billing export dataset
gcloud alpha billing accounts describe <ACCOUNT_ID>

# List active resources that incur cost
gcloud compute instances list --format="table(name,zone,machineType,status)"
gcloud sql instances list --format="table(name,region,tier,state)"
gcloud container clusters list --format="table(name,zone,currentNodeCount,status)"
gcloud compute disks list --format="table(name,zone,sizeGb,status,users)"
gcloud compute addresses list --format="table(name,region,status,users)"
```

**Azure:**
```bash
# Consumption usage for current billing period
az consumption usage list --top 100 --output table

# Cost by resource group
az cost management query \
  --type Usage \
  --timeframe MonthToDate \
  --dataset-grouping name="ResourceGroup" type="Dimension"

# List resources by group
az resource list --output table
```

**DigitalOcean:**
```bash
# Recent invoices
doctl invoice list

# Current balance
doctl balance get

# List resources
doctl compute droplet list --format Name,Region,Size,Status
doctl databases list --format Name,Engine,Size,Region,Status
doctl kubernetes cluster list --format Name,Region,NodePools
doctl compute volume list --format Name,Region,Size,DropletIDs
doctl compute load-balancer list --format Name,Region,Status
```

**Kubernetes (if applicable, regardless of cloud provider):**
```bash
# Node-level resource usage
kubectl top nodes

# Pod-level resource usage (sorted by memory consumption)
kubectl top pods --all-namespaces --sort-by=memory

# Resource requests vs limits for all pods
kubectl get pods --all-namespaces -o custom-columns=\
  NAMESPACE:.metadata.namespace,\
  POD:.metadata.name,\
  CPU_REQ:.spec.containers[*].resources.requests.cpu,\
  CPU_LIM:.spec.containers[*].resources.limits.cpu,\
  MEM_REQ:.spec.containers[*].resources.requests.memory,\
  MEM_LIM:.spec.containers[*].resources.limits.memory

# PersistentVolumeClaims and their sizes
kubectl get pvc --all-namespaces -o custom-columns=\
  NAMESPACE:.metadata.namespace,\
  NAME:.metadata.name,\
  SIZE:.spec.resources.requests.storage,\
  STATUS:.status.phase
```

If any command fails due to permissions or authentication, note the failure and move on. Do not let a single failed command block the entire analysis.

#### 3. Break Down Costs

Organize the gathered data into a clear breakdown:

**By service type:**
- Compute (VMs, containers, serverless functions, CI/CD minutes)
- Storage (block storage, object storage, snapshots, backups)
- Networking (load balancers, data transfer, DNS, CDN, NAT gateways, static IPs)
- Database (managed databases, caches, message queues)
- Other (monitoring, logging, support plans, domain registration, etc.)

**By environment (if distinguishable):**
- Production
- Staging
- Development
- Shared/infrastructure (networking, DNS, monitoring that spans environments)

Tags, resource naming conventions, or separate accounts/projects are the primary way to distinguish environments. If environments cannot be distinguished, note this as a gap and recommend implementing resource tagging.

**By cost type (convention 39):**
- **Fixed costs**: Reserved instances, committed use discounts, static infrastructure (load balancers, NAT gateways, static IPs), base support plans, always-on instances
- **Variable costs**: On-demand compute, data transfer, storage growth, serverless invocations, CI/CD minutes, API calls, storage I/O operations

#### 4. Identify Waste

Check for each waste category defined in conventions 35-38:

**Idle resources (convention 35):**
- **Unused load balancers**: Load balancers with zero or near-zero traffic
  - AWS: `aws elbv2 describe-load-balancers` combined with CloudWatch `RequestCount` metrics
  - GCP: `gcloud compute forwarding-rules list`
  - Check for load balancers with no registered targets or no healthy targets
- **Detached volumes**: Block storage not attached to any instance
  - AWS: `aws ec2 describe-volumes --filters Name=status,Values=available`
  - GCP: `gcloud compute disks list --filter="NOT users:*"`
  - DigitalOcean: `doctl compute volume list` and check for empty DropletIDs
- **Stopped instances**: VMs that have been stopped for extended periods but not terminated (still incur storage costs)
  - AWS: `aws ec2 describe-instances --filters Name=instance-state-name,Values=stopped`
  - GCP: `gcloud compute instances list --filter="status=TERMINATED"`
- **Unused Elastic IPs / static IPs**: Allocated but not associated with a running instance
  - AWS: `aws ec2 describe-addresses` and filter for those without `InstanceId` or `AssociationId`
  - GCP: `gcloud compute addresses list --filter="status=RESERVED"`
- **Old snapshots**: Snapshots older than retention policy (or older than 90 days if no policy)
  - AWS: `aws ec2 describe-snapshots --owner-ids self` and filter by `StartTime`
- **Unused NAT gateways**: NAT gateways with minimal or zero traffic
  - AWS: `aws ec2 describe-nat-gateways` and check CloudWatch `BytesOutToDestination`

**Oversized resources (convention 36):**
- Instances with consistently low CPU utilization (< 10% average over 7+ days)
  - AWS: Check CloudWatch `CPUUtilization` metric
  - GCP: Check Compute Engine monitoring metrics
- Instances with consistently low memory utilization (if memory metrics are available)
- Database instances with excessive provisioned capacity vs. actual connection count or query volume
- Over-provisioned Kubernetes node pools (many nodes with low pod density or low resource utilization)
- Over-provisioned storage (volumes using < 20% of allocated capacity)

**Unused storage:**
- Old container images in registries (ECR, GCR, GHCR) without lifecycle policies
- Old CI/CD artifacts that are not cleaned up
- Unused S3 buckets or GCS buckets with no recent access
- Database snapshots beyond retention needs

**Dev/staging running 24/7 (convention 38):**
- Check if non-production environments run continuously
- Estimate savings from auto-scaling down outside business hours:
  - Weekday nights only (off 12 hours/day, 5 days): ~36% savings
  - Weekday business hours only (off nights + weekends): ~60% savings
  - On-demand only (spin up as needed): up to ~80% savings for rarely used environments
- Check for existing auto-scaling schedules or Lambda-based stop/start automation
- Check for Kubernetes cluster autoscaler or Karpenter configuration

For each waste item found, estimate the monthly cost being wasted. Use pricing from the gathered cost data, or reference the resource size and public pricing for estimates.

#### 5. Estimate Savings

For each finding, calculate or estimate potential monthly savings:
- **Idle resources**: Full cost of the resource (it provides zero value while running)
- **Oversized resources**: Cost difference between current size and recommended right-sized alternative
- **Dev/staging scheduling**: Current cost multiplied by percentage of time it could be powered off
- **Old snapshots/volumes**: Storage cost per GB multiplied by total size
- **Container image cleanup**: Registry storage costs (usually small but adds up in large organizations)

Sum up the total potential savings to give a headline number. Also compute annual savings for impact framing.

Distinguish between:
- **Immediate savings**: Deleting truly idle resources (low risk, high confidence)
- **Near-term savings**: Right-sizing after validation (moderate risk, needs monitoring to confirm)
- **Strategic savings**: Reserved instances, architectural changes (requires commitment, highest potential savings)

#### 6. Produce Prioritized Recommendations

Rank recommendations by: estimated monthly savings multiplied by ease of implementation. Group into tiers:

**Quick wins (immediate):**
- Delete idle resources (detached volumes, unused LBs, old snapshots)
- Release unused static IPs
- Clean up old container images
- These are low-risk, no-downtime changes

**Right-sizing (this quarter):**
- Downsize oversized instances after confirming utilization patterns
- Adjust Kubernetes resource requests to match actual usage
- Resize database instances
- These require monitoring data to validate the recommendation

**Scheduling (this month):**
- Set up auto-stop for dev/staging environments outside business hours
- Configure cluster autoscaler for Kubernetes
- These save money without reducing capability during work hours

**Architectural (next quarter):**
- Purchase reserved instances or savings plans for stable workloads
- Migrate to spot/preemptible instances for fault-tolerant workloads
- Consolidate multiple small instances into fewer larger ones (or vice versa)
- These require planning and may have upfront costs

For each recommendation, provide:
- What to do (specific action)
- Expected monthly and annual savings
- Risk level (low/medium/high — could this cause an outage or data loss?)
- Effort required (quick fix / moderate / significant)
- Implementation steps (specific commands or process)
- Rollback plan (how to undo if something goes wrong)

## Output Format

Write the analysis to `.deepwork/artifacts/platform_engineer/cloud_spend/spend_analysis.md`. Create parent directories if they do not exist.

```markdown
# Cloud Spend Analysis

**Generated**: YYYY-MM-DD HH:MM
**Repository**: <repo name>
**Cloud Provider(s)**: <AWS / GCP / Azure / DigitalOcean / etc.>
**Analysis Period**: <date range analyzed>

## Cost Breakdown

### By Service Type

| Service Category | Monthly Cost | % of Total | Trend |
|-----------------|-------------|-----------|-------|
| Compute | $X,XXX | XX% | stable / increasing / decreasing |
| Storage | $X,XXX | XX% | ... |
| Networking | $X,XXX | XX% | ... |
| Database | $X,XXX | XX% | ... |
| Other | $X,XXX | XX% | ... |
| **Total** | **$X,XXX** | **100%** | ... |

### By Environment

| Environment | Monthly Cost | % of Total | Notes |
|-------------|-------------|-----------|-------|
| Production | $X,XXX | XX% | |
| Staging | $X,XXX | XX% | |
| Development | $X,XXX | XX% | |
| Shared/Infra | $X,XXX | XX% | |
| **Total** | **$X,XXX** | **100%** | |

*If environments cannot be distinguished, note why and recommend implementing resource tagging.*

### Fixed vs. Variable (Convention 39)

| Cost Type | Monthly Cost | % of Total | Components |
|-----------|-------------|-----------|------------|
| Fixed | $X,XXX | XX% | <reserved instances, LBs, static IPs, etc.> |
| Variable | $X,XXX | XX% | <on-demand compute, data transfer, etc.> |

## Waste Identification

### Idle Resources (Convention 35)

| Resource | Type | Region | Monthly Cost | Idle Since | Evidence |
|----------|------|--------|-------------|-----------|---------|
| <name/id> | <LB/volume/instance/etc.> | <region> | $XX | <date or duration> | <why it is idle> |
| ... | ... | ... | ... | ... | ... |
| | | | **$XX total** | | |

### Oversized Resources (Convention 36)

| Resource | Current Size | Avg Utilization | Recommended Size | Monthly Savings |
|----------|-------------|----------------|-----------------|----------------|
| <name/id> | <instance type> | <CPU%/Mem%> | <recommended type> | $XX |
| ... | ... | ... | ... | ... |
| | | | | **$XX total** |

### Unused Storage

| Resource | Type | Size | Last Accessed | Monthly Cost |
|----------|------|------|--------------|-------------|
| <name/id> | <snapshot/volume/bucket> | <size> | <date or "unknown"> | $XX |
| ... | ... | ... | ... | ... |
| | | | | **$XX total** |

### Dev/Staging Always-On (Convention 38)

| Environment | Resources | Current Monthly Cost | Potential Savings (scheduling) | Savings % |
|-------------|-----------|---------------------|-------------------------------|-----------|
| <staging> | <list resources> | $XX | $XX | XX% |
| ... | ... | ... | ... | ... |

## Recommendations

*Ordered by estimated monthly savings, highest first.*

| # | Recommendation | Monthly Savings | Annual Savings | Risk | Effort | Category |
|---|---------------|----------------|---------------|------|--------|----------|
| 1 | <specific action> | $XXX | $X,XXX | low/med/high | quick/moderate/significant | <idle/oversize/storage/scheduling> |
| 2 | ... | ... | ... | ... | ... | ... |
| ... | ... | ... | ... | ... | ... | ... |
| | **Total Potential Savings** | **$X,XXX** | **$XX,XXX** | | | |

### Recommendation Details

#### 1. <Recommendation title>
- **Action**: <what to do>
- **Savings**: $XXX/month ($X,XXX/year)
- **Risk**: <low/medium/high> — <why>
- **Implementation**:
  ```bash
  <specific commands or steps>
  ```
- **Rollback**: <how to undo if needed>

#### 2. <Recommendation title>
...

## Cost Trend

*If historical data is available (3+ months):*

| Month | Total Cost | Change | Notable Events |
|-------|-----------|--------|---------------|
| <month> | $X,XXX | — | baseline |
| <month> | $X,XXX | +X% / -X% | <new service launched, traffic spike, etc.> |
| <month> | $X,XXX | +X% / -X% | ... |

*If historical data is not available:*

> Historical cost data was not available. Recommend setting up monthly cost tracking
> and cost anomaly alerts (convention 37) to establish a baseline for future analysis.

## Data Collection Notes

- **Data source**: <CLI tool / billing export / user-provided>
- **Limitations**: <any commands that failed, data gaps, permissions issues>
- **Confidence**: <high if from billing API, medium if estimated from resource inventory, low if user-provided summary>
- **Recommendations for future analysis**: <set up cost allocation tags, enable billing export, configure anomaly detection>
```

## Quality Criteria

- **Cost Data Gathered**: Current cloud costs are documented with a breakdown by service type. If raw cost data is unavailable, the report clearly states why and documents whatever data was obtainable (e.g., resource inventory with estimated costs from public pricing).
- **Waste Identified**: Idle, oversized, and unused resources are specifically identified per conventions 35-38. Each waste item includes the resource identifier, type, estimated monthly cost, and evidence for why it is considered waste. If no waste is found, this is stated explicitly rather than leaving the section empty.
- **Savings Estimated**: Every recommendation includes a dollar estimate for potential monthly and annual savings. Estimates are based on actual pricing data where possible. The total potential savings is summed to give a headline number.
- **Fixed vs. Variable Classified**: Costs are categorized as fixed or variable per convention 39, helping the user understand which costs can be reduced through optimization vs. which require contract or commitment changes.
- **Recommendations Are Actionable**: Each recommendation includes specific actions (commands, console steps), risk assessment, and rollback instructions. A reader can act on any recommendation without additional research.
- **Prioritized by Impact**: Recommendations are ordered by estimated monthly savings so the highest-impact items are addressed first. Quick wins are separated from longer-term optimizations.
- **No Destructive Actions Taken**: This step only reads cost data and resource metadata. No resources are terminated, resized, or modified. Recommendations describe what to do — the user decides whether to act.

## Context

This step is the sole working step in the `cloud_spend` workflow (after `gather_context`). It produces a standalone cost analysis document.

Cloud cost analysis depends heavily on what tools and permissions are available. The step MUST degrade gracefully:
- If the cloud CLI is available with billing permissions: full automated analysis with precise cost data
- If the cloud CLI is available but billing is restricted: resource inventory with estimated costs from public pricing
- If no cloud CLI is available: ask the user for billing data and analyze whatever they provide
- If there is no cloud infrastructure: document this and produce a minimal report

The waste categories from conventions 35-38 provide the framework for identifying savings opportunities. Convention 39 (fixed vs. variable cost distinction) is important for understanding which costs are optimizable through usage changes vs. which require commitment changes (reserved instances, savings plans).

For Kubernetes environments, cost analysis has an additional dimension. The cluster cost is a fixed cloud expense, but the workload distribution within the cluster determines efficiency. Over-provisioned node pools or workloads with excessive resource requests (but low actual usage) represent hidden waste that does not appear in cloud billing alone. The `kubectl top` commands help surface this internal inefficiency.

The savings estimates do not need to be precise to the penny. Order-of-magnitude accuracy is sufficient for prioritization — the difference between "$50/month" and "$500/month" matters for prioritization, but the difference between "$487" and "$512" does not. When exact pricing is not available, use conservative estimates and note the confidence level.
