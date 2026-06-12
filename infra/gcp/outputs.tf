output "deployment_enabled" {
  description = "Confirms whether resource counts are enabled."
  value       = var.enable_deployment
}

output "api_service_name" {
  description = "Future Cloud Run API service name."
  value       = try(google_cloud_run_v2_service.api[0].name, null)
}

output "operations_job_name" {
  description = "Future Cloud Run operations job name."
  value       = try(google_cloud_run_v2_job.operations[0].name, null)
}

