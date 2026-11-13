# Phase 3 cloud cost estimate

Estimate checked on **November 13, 2026** for **AWS us-east-1 (N. Virginia)**. **The current project budget is R$0: AWS is an architecture reference only. Do not create an AWS account for this exercise, provision resources, deploy publicly, or activate paid subscriptions.** Completing Phase 3 requires local runtime validation, Terraform mock tests and documented trade-offs; it does not require an AWS account or domain.

The figures below are a theoretical future estimate, not actual spending, a quotation or evidence of resources created. No Free Tier or promotional credit is assumed to make a paid architecture fit the zero-cost budget.

The reference design is one Linux x86 EC2 `t3.small`, one private Single-AZ RDS PostgreSQL `db.t4g.micro`, encrypted storage, two Secrets Manager secrets, and private S3 state/release buckets. It has no NAT gateway, load balancer, Kubernetes cluster, paid monitoring stack, or reserved-capacity commitment. Its proposed public HTTPS endpoint terminates at Caddy on EC2; the implemented demonstration uses local TLS instead.

## Always-on baseline

Assumptions: 730 running hours per month; 16 GiB EC2 root volume; 20 GiB RDS gp3; one public IPv4 address; two secrets; 5 GiB total S3 Standard storage including retained versions; 1,000 S3 write/list requests, 10,000 S3 reads, and 1,000 secret API calls. No introductory Free Tier, credits, or reservations are deducted.

| Component | Unit price / formula | Estimated USD/month | Official source |
| --- | --- | ---: | --- |
| EC2 `t3.small`, Linux On-Demand | 730 × $0.0208/hour | $15.18 | [AWS regional Linux EC2 price feed](https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/US%20East%20%28N.%20Virginia%29/Linux/index.json), SKU `QA3NBPZEQKZ2K9AR` |
| EC2 root EBS gp3 | 16 × $0.08/GB-month; included baseline performance | $1.28 | [AWS EBS gp3](https://aws.amazon.com/ebs/general-purpose/) |
| RDS PostgreSQL `db.t4g.micro`, Single-AZ | 730 × $0.016/hour | $11.68 | [AWS regional RDS price list](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/us-east-1/index.json), SKU `9HPEGXQTDDGH53C9` |
| RDS gp3 database storage | 20 × $0.115/GB-month | $2.30 | [AWS regional RDS price list](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/us-east-1/index.json), SKU `KYVYY29G957PKY3B` |
| Public IPv4 / Elastic IP | 730 × $0.005/hour | $3.65 | [AWS VPC IPv4 pricing](https://aws.amazon.com/vpc/pricing/) |
| Secrets Manager secret storage | 2 × $0.40/secret-month | $0.80 | [AWS Secrets Manager pricing](https://aws.amazon.com/secrets-manager/pricing/) |
| Secrets Manager API calls | 1,000 ÷ 10,000 × $0.05 | $0.005 | [AWS Secrets Manager pricing](https://aws.amazon.com/secrets-manager/pricing/) |
| S3 Standard state/releases | 5 × $0.023/GB-month | $0.115 | [AWS regional S3 price list](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/us-east-1/index.json), SKU `WP9ANXZGBYYSGJEA` |
| S3 requests | 1,000 × $0.000005 + 10,000 × $0.0000004 | $0.009 | [AWS regional S3 price list](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/us-east-1/index.json), SKUs `E9YHNFENF4XQBZR6` / `ZWQ6Q48CRJXX4FXE` |
| **Baseline, rounded after summing** | | **$35.02** | |

The downloaded official RDS list was published `2026-11-12T22:34:41Z`; the S3 list was published `2026-11-09T15:43:10Z`. The EC2 regional Linux feed was rechecked on November 13 and returned `0.0208000000` for `t3.small`, rate code `QA3NBPZEQKZ2K9AR.JRTCKXETXF.6YS6EN2CT7`. Public pricing pages and feeds may disagree or change; these are dated estimate inputs, not a guaranteed future rate. A future `/current/` response can differ. Recheck the linked rates and final resource sizes if a separate future project ever authorizes deployment. RDS storage uses its own $0.115 rate, not EC2 EBS's $0.08 rate.

A theoretical operating envelope would be **$45–50/month before tax**, allowing some traffic, retained backups and request growth. This is an estimate, not an approved budget or a spending cap. A budget alert also does not stop resources automatically. **Neither the $35.02 baseline nor this envelope is compatible with this execution's R$0 cloud budget; therefore no deployment is performed.**

## Costs outside the baseline

- RDS `t4g` instances run in Unlimited mode. Surplus CPU is **$0.075 per vCPU-hour** beyond the rolling baseline. Ten billed surplus vCPU-hours add $0.75. EC2 is configured for Standard credits to avoid its separate surplus-credit charges; that setting does not change RDS behavior. Sustained CPU demand may instead require a larger database. [AWS RDS PostgreSQL pricing](https://aws.amazon.com/rds/postgresql/pricing/)
- RDS backups exceeding the applicable regional allocation cost **$0.095 per additional GB-month**; 20 billed GiB add $1.90. The normal backup allocation is shared across account/region snapshots and is not an introductory credit. Do not assume it is unused. Retained final snapshots can continue billing after the DB is deleted. [AWS RDS price list](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/us-east-1/index.json), SKU `6W8ECRFVDATCER7J`; [backup allocation and retained snapshots](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.html)
- Internet egress, cross-AZ database traffic, snapshot exports/restores and extra S3 versions depend on actual use. Place EC2 and the active RDS instance in the same AZ when the reviewed plan permits it; do not assume an account-level transfer allowance is available. Recalculate from [EC2 pricing](https://aws.amazon.com/ec2/pricing/on-demand/), [RDS pricing](https://aws.amazon.com/rds/postgresql/pricing/) and [S3 pricing](https://aws.amazon.com/s3/pricing/).
- A domain must already be owned or purchased separately. Its registration/renewal price depends on the registrar and TLD and is excluded. If an existing Route 53 hosted zone is used, record creation does not create another zone. A newly requested zone would add **$0.50/month**, plus standard DNS queries at **$0.40/million** in the initial tier. The default design does not create that zone. [AWS Route 53 pricing](https://aws.amazon.com/route53/pricing/)
- AWS taxes, duties, currency conversion, payment-provider charges, optional support plans and any unrelated account resources are excluded. Region changes require a fresh estimate; these figures do not price São Paulo.
- Upgrading PostgreSQL after standard support ends is an operational obligation. This estimate excludes RDS Extended Support; selecting an unsupported major version may add charges. [RDS pricing and support charges](https://aws.amazon.com/rds/postgresql/pricing/)

## Managed versus self-managed database

| Option | Benefit | Cost / operational consequence |
| --- | --- | --- |
| **Private RDS, reference IaC default** | Managed database storage, backups and maintenance; separate network/security boundary and credentials | Adds approximately $13.98/month for instance/storage before backup and credit usage; Single-AZ still permits downtime |
| PostgreSQL container on the EC2 host | Avoids the RDS instance/storage line items | Shares the application's failure domain and memory; maintainer must implement off-host backups, restore drills, patching and disk monitoring; increasing EC2 size/storage can consume the apparent saving |

The RDS choice demonstrates the managed-database trade-off and clearer data protection; local Docker PostgreSQL is used for the actual zero-cost demonstration. The reference is **not high availability**: one app host and one Single-AZ DB can each cause downtime. Multi-AZ, NAT, a load balancer or replicas would increase both scope and costs.

## Pausing and teardown

Stopping EC2 does not remove EBS or release its Elastic IP; those line items can continue. A stopped RDS instance still bills storage/backups and can remain stopped for at most seven consecutive days before restarting. Therefore, a stopped environment is not zero-cost or a durable spending control. [AWS VPC pricing](https://aws.amazon.com/vpc/pricing/), [RDS stop behavior](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_StopInstance.html)

In a future deployment, destroying the application stack would stop more recurring charges, but retained snapshots, secrets awaiting deletion, S3 object versions and the separate state bucket could remain. [CLOUD_RUNBOOK.md](CLOUD_RUNBOOK.md) describes the retention/teardown considerations. No cloud teardown is needed or run in this exercise because no cloud resources are created. Local smoke-test containers are separately disposable.

## Reference resource inventory

For architecture review, the two Terraform stacks describe the following logical inventory. The current permitted operations are local validation and mock tests only:

- One EC2 host, one 16 GiB encrypted root volume, one Elastic IP, one private Single-AZ RDS instance and 20 GiB database storage.
- Two private, encrypted, versioned S3 buckets in total: bootstrap remote state plus application releases.
- One RDS-managed master secret and one application secret; no plaintext secret values in Terraform configuration/state.
- One VPC, one public subnet, two private DB subnets, an internet gateway, explicit route associations and two purpose-specific security groups. No public RDS endpoint, inbound SSH, NAT gateway or load balancer.
- IAM instance profile and narrow policies, manual DNS output, backup retention, snapshot retention and deletion protection. No Route 53 hosted zone is created.
- A future real plan would require review of its exact add/change/destroy resource counts, costs, restore/teardown strategy, intended hostname and operating period. These service counts are not a substitute for Terraform's individual resource actions and are not a claim that a real plan ran.

The current user instruction prohibits provisioning and paid services. The estimate and local IaC validation do not authorize an apply, deployment, account creation or subscription. There are no actual cloud costs asserted by this document.
