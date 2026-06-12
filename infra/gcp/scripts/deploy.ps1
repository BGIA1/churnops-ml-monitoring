$ErrorActionPreference = "Stop"

if ($env:CHURNOPS_ALLOW_GCP_APPLY -ne "REVIEWED-MANUAL-APPLY") {
    throw "Deployment is locked. Complete review and set CHURNOPS_ALLOW_GCP_APPLY explicitly."
}

throw @"
This repository intentionally does not automate terraform apply.
After security, cost, IAM, OIDC, plan, and teardown review, an authorized operator may construct
the apply command manually. No cloud command has been executed by this template.
"@

