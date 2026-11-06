# WSL2 and AWS CLI administration runbook

This runbook configures one WSL2 Ubuntu terminal to administer one or two AWS accounts without storing permanent AWS access keys.

## 1. Prepare WSL2

In Windows PowerShell (administrator):

    wsl --install -d Ubuntu

Restart if Windows requests it, open Ubuntu, and create the Linux user. In Ubuntu:

    sudo apt update && sudo apt upgrade -y
    sudo apt install -y git curl unzip jq ca-certificates gnupg lsb-release

Use the Linux filesystem (for example ~/src/wunderdesk) for the repository and Terraform state cache, not /mnt/c, to avoid WSL filesystem performance issues.

## 2. Install AWS CLI v2

In Ubuntu/WSL2:

    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    sudo ./aws/install
    aws --version

For ARM64 WSL, use the AWS CLI ARM64 installer instead of x86_64.

## 3. Install Terraform

Install Terraform from HashiCorp's official Linux repository and pin the version used by the repository. Do not use an unpinned latest version in CI and local production work.

    terraform version

## 4. Configure named AWS profiles

Preferred method: AWS IAM Identity Center (SSO), not IAM user access keys.

Run:

    aws configure sso

Use the IAM Identity Center start URL and Identity Center Region supplied by the account administrator. The Identity Center Region is not necessarily the workload Region. Select the account and role for the primary account, and name the profile:

    wunder-primary

Repeat for the standby account and name the profile:

    wunder-standby

If both accounts are in the same IAM Identity Center organization, the same SSO session may be reused with two account-specific profiles. If they are separate standalone accounts, configure the appropriate SSO session for each.

Log in and verify each identity:

    aws sso login --profile wunder-primary
    aws sts get-caller-identity --profile wunder-primary

    aws sso login --profile wunder-standby
    aws sts get-caller-identity --profile wunder-standby

The account ID returned by get-caller-identity must match the account being configured. Stop if it does not.

## 5. Switch the active terminal profile safely

Prefer passing --profile on every AWS command:

    aws ec2 describe-instances --region eu-central-1 --profile wunder-primary
    aws ec2 describe-instances --region eu-central-1 --profile wunder-standby

For a temporary shell selection:

    export AWS_PROFILE=wunder-primary
    aws sts get-caller-identity

    export AWS_PROFILE=wunder-standby
    aws sts get-caller-identity

    unset AWS_PROFILE

Check for environment variables that override profiles:

    env | grep '^AWS_'

Do not export AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY or AWS_SESSION_TOKEN for routine administration. If stale variables exist, unset them before testing named profiles:

    unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN

## 6. Clone the repository

    mkdir -p ~/src
    cd ~/src
    git clone https://github.com/Samoolino/Wunderdesk.git
    cd Wunderdesk

Use GitHub CLI or an approved Git credential manager for authenticated pushes. Never put a GitHub token in a remote URL or shell history.

## 7. Account inventory before provisioning

Run each command with an explicit profile:

    aws sts get-caller-identity --profile wunder-primary
    aws ec2 describe-availability-zones --region eu-central-1 --profile wunder-primary
    aws ec2 describe-addresses --region eu-central-1 --profile wunder-primary
    aws service-quotas list-service-quotas --service-code ec2 --profile wunder-primary

Repeat for wunder-standby.

Confirm:
- Account identity and permissions.
- Region and availability zones.
- EC2 vCPU quota and instance availability.
- Elastic IP quota.
- Billing plan/payment method and AWS credits.
- IAM permissions for VPC, EC2, EIP, Secrets Manager, KMS, CloudWatch and deployment.
- Both outbound EIPs can be allowlisted in the WunderTrading API key.

## 8. Terraform state and account separation

Use separate state for each account, for example:
- primary state key: wunderdesk/primary/terraform.tfstate
- standby state key: wunderdesk/standby/terraform.tfstate

Use a remote backend with encryption, versioning, access restrictions and state locking supported by the pinned Terraform version. Do not commit state files, plan files, tfvars containing secrets, or local .terraform directories.

Run plans with explicit profiles:

    AWS_PROFILE=wunder-primary terraform plan -var-file=env/primary.tfvars
    AWS_PROFILE=wunder-standby terraform plan -var-file=env/standby.tfvars

Review the plan and account identity before every apply. Never run apply against both accounts concurrently for the same deployment change.

## 9. Post-deployment verification

From each worker, verify:
- Instance role credentials are available through instance metadata and no static AWS keys are present.
- The outbound public IP equals that account's assigned Elastic IP.
- HTTPS requests to the WunderTrading API succeed using read-only scope first.
- Secrets Manager access is limited to the required secret.
- CloudWatch heartbeat and status alarms are reporting.
- The standby is not permitted to submit orders without the current execution lease.

## 10. Credential and recovery rules

- Never share AWS root credentials.
- Enable MFA on root and privileged identities.
- Use IAM Identity Center and temporary sessions for people.
- Use instance profiles for EC2 applications.
- Rotate WunderTrading credentials if they are exposed.
- Keep recovery codes and billing contacts outside the repository.
- If an AWS account is suspended or cannot authenticate, do not assume the worker can drain gracefully. The standby must already be provisioned, allowlisted and tested.
