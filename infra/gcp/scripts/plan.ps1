$ErrorActionPreference = "Stop"

$required = @(
    "CHURNOPS_GCP_PROJECT_ID",
    "CHURNOPS_GCP_REGION",
    "CHURNOPS_CONTAINER_IMAGE",
    "CHURNOPS_ARTIFACT_BUCKET"
)

foreach ($name in $required) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name))) {
        throw "Missing required environment variable: $name"
    }
}

Write-Warning "Template plan only. This script keeps enable_deployment=false and creates nothing."
terraform init -backend=false
terraform plan `
    -var="enable_deployment=false" `
    -var="project_id=$env:CHURNOPS_GCP_PROJECT_ID" `
    -var="region=$env:CHURNOPS_GCP_REGION" `
    -var="container_image=$env:CHURNOPS_CONTAINER_IMAGE" `
    -var="artifact_bucket_name=$env:CHURNOPS_ARTIFACT_BUCKET"

