# AWS reference infrastructure — R$0 portfolio mode

This directory is an infrastructure design and an account-free test target. **Do not provision AWS resources, initialize the remote S3 backend, or run Terraform apply for this project.** The current budget is R$0. An AWS account, AWS credentials, domain, Free Tier allowance, paid subscription, and actual deployment are not required to complete Phase 3.

The application continues to run locally through the root `compose.yaml`. The optional production images and local TLS smoke test also run entirely in Docker. See [CLOUD_RUNBOOK.md](../../docs/CLOUD_RUNBOOK.md), [CLOUD_COSTS.md](../../docs/CLOUD_COSTS.md), and [PHASE3_VALIDATION.md](../../docs/PHASE3_VALIDATION.md) for the architecture, theoretical future cost, and actual validation evidence.

## Module boundaries

| Directory | Proposed resources | Account-free evidence |
| --- | --- | --- |
| `bootstrap/` | Private versioned S3 state bucket, SSE-S3 encryption, public-access block, TLS-only bucket policy and deletion protection | Two mocked plan runs verify the state protections and reject an ambiguous account ID |
| `app/` | VPC, one public application subnet, two private database subnets, EC2/EIP, private managed PostgreSQL, scoped instance role, app-secret metadata and private versioned release bucket | Six mocked plan runs verify encryption/private TLS DB, IAM/instance/storage controls, and invalid account/domain/engine/AZ inputs |

The state bootstrap is deliberately separate from the application configuration. `app/versions.tf` declares an S3 backend, but local checks always initialize with `-backend=false`; no S3 request is needed. The `.example` backend files are documentation only and must not be copied into active backend configuration for the zero-budget demonstration. S3-native `.tflock` locking is the future backend design; no DynamoDB table or managed Terraform service is proposed.

The network design has no NAT gateway, load balancer, SSH ingress, or public database port. Only proposed web ports 80/443 are public; port 80 supports ACME and HTTPS redirects. The RDS security group accepts PostgreSQL only from the application security group, and its subnets have an explicitly empty Internet/NAT route table. Database and host disks are encrypted. The host requires IMDSv2 and uses a hop limit of one; an application container is not intended to inherit the host's AWS credentials.

The instance IAM policy can read only the dedicated application secret and `releases/` objects in its release bucket. It cannot read the RDS administrator secret. SSM channel APIs use the minimum required wildcard-resource actions because those APIs do not support resource-level ARNs; they are not `ssm:*` grants. Future operator permissions for provisioning, SSM administration and initial database-user creation are separate trusted duties, not privileges granted to the application role.

RDS manages its administrator password through Secrets Manager. Terraform defines only application-secret metadata; it does not define a secret version or a plaintext application password. An eventual operator must create a separate database role/schema for migrations and runtime work, and populate its credential outside Terraform. No such AWS bootstrap was executed or automated in this zero-budget phase.

## Verify the pinned tool

[tool-versions.json](tool-versions.json) pins Terraform 1.17.2, AWS provider 6.73.0 and the checksum of the future host's Docker Compose binary. Terraform archive checksums come from the linked official HashiCorp SHA256SUMS manifest. Downloading the CLI and provider requires ordinary Internet access to public registries, but never an AWS account. Subsequent mocked tests do not exercise AWS service APIs.

Windows PowerShell example, from the repository root:

```powershell
$tools = Get-Content infra/terraform/tool-versions.json -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Force .local/terraform | Out-Null
$archive = '.local/terraform/terraform.zip'
Invoke-WebRequest "https://releases.hashicorp.com/terraform/$($tools.terraform.version)/terraform_$($tools.terraform.version)_windows_amd64.zip" -OutFile $archive
if ((Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $tools.terraform.windows_amd64_sha256) { throw 'Terraform checksum mismatch' }
Expand-Archive -LiteralPath $archive -DestinationPath .local/terraform -Force
& .local/terraform/terraform.exe version
```

Linux x86_64 example, from the repository root (requires `curl`, `python3` and `unzip`):

```sh
version=$(python3 -c 'import json; print(json.load(open("infra/terraform/tool-versions.json"))["terraform"]["version"])')
checksum=$(python3 -c 'import json; print(json.load(open("infra/terraform/tool-versions.json"))["terraform"]["linux_amd64_sha256"])')
mkdir -p .local/terraform
curl --fail --location "https://releases.hashicorp.com/terraform/$version/terraform_${version}_linux_amd64.zip" --output .local/terraform/terraform.zip
printf '%s  %s\n' "$checksum" .local/terraform/terraform.zip | sha256sum --check - || exit "$?"
unzip -o .local/terraform/terraform.zip -d .local/terraform
.local/terraform/terraform version
```

The CI workflow performs the same pinned checksum verification. Do not install or use an AWS credential provider merely to run these tests.

## Run only the account-free checks

PowerShell, from the repository root:

```powershell
$env:AWS_EC2_METADATA_DISABLED = 'true'
& .local/terraform/terraform.exe fmt -check -recursive infra/terraform
if ($LASTEXITCODE -ne 0) { throw 'Terraform formatting failed' }
foreach ($module in @('bootstrap', 'app')) {
    & .local/terraform/terraform.exe "-chdir=infra/terraform/$module" init -backend=false -input=false -lockfile=readonly
    if ($LASTEXITCODE -ne 0) { throw "Initialization failed: $module" }
    & .local/terraform/terraform.exe "-chdir=infra/terraform/$module" validate -no-color
    if ($LASTEXITCODE -ne 0) { throw "Validation failed: $module" }
    & .local/terraform/terraform.exe "-chdir=infra/terraform/$module" test -no-color
    if ($LASTEXITCODE -ne 0) { throw "Mock tests failed: $module" }
}
```

Linux x86_64, using the verified CLI above:

```sh
export AWS_EC2_METADATA_DISABLED=true
.local/terraform/terraform fmt -check -recursive infra/terraform || exit "$?"
for module in bootstrap app; do
  .local/terraform/terraform -chdir="infra/terraform/$module" init -backend=false -input=false -lockfile=readonly &&
  .local/terraform/terraform -chdir="infra/terraform/$module" validate -no-color &&
  .local/terraform/terraform -chdir="infra/terraform/$module" test -no-color || exit "$?"
done
```

Each `.tftest.hcl` contains `mock_provider "aws"` with plan-time overrides. **Every run uses `command = plan`**; no test run requests an apply operation. Terraform's messages such as “tearing down” refer to its isolated test context, not deletion of cloud resources. Example account/AMI/domain/ARN values are placeholders. Passing a mock test demonstrates configuration contracts, not that an AMI, engine minor version, region quota, cloud network path or real deployment was tested.

Commit both `.terraform.lock.hcl` files. They constrain the provider and include signed provider checksums for platform-independent verification. Keep `.terraform/`, real `backend.hcl`, `*.tfvars`, `*.tfvars.json`, state files and saved plans out of Git. Never place access keys, tokens, passwords or database URLs in Terraform examples, backend arguments or state configuration.

## Future deployment considerations, not an execution step

The Terraform sources are intended to make a future independently authorized deployment reviewable. They are not an authorization to spend money or a claim that AWS is currently running ForgeBoard. Any future operator would have to revisit costs, choose an available reviewed x86 AL2023 AMI and RDS PostgreSQL 16 minor version, verify DNS ownership and IAM permissions, provision/review the state backend, create a least-privilege DB role, provide TLS CA material and load reviewed application images. Those operations are intentionally outside this phase.

The reference protects data from accidental deletion: RDS deletion protection is enabled, a final snapshot is mandatory, automated backups are retained, secret deletion has a recovery period, and the state bucket has `prevent_destroy`. These protections mean a future teardown is a deliberate multistep operation, not a command promised to remove every billable snapshot/version automatically. No teardown was executed or needed because no AWS resources were created.

Official references: [Terraform mock providers](https://developer.hashicorp.com/terraform/language/tests/mocking), [S3 backend and native state locking](https://developer.hashicorp.com/terraform/language/backend/s3), [RDS-managed Secrets Manager passwords](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-secrets-manager.html).
