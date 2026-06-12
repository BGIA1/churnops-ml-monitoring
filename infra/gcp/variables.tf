variable "enable_deployment" {
  description = "Safety gate. Keep false until an approved manual deployment."
  type        = bool
  default     = false
}

variable "project_id" {
  description = "Target GCP project ID. No project is hardcoded."
  type        = string
  default     = null
  nullable    = true
}

variable "region" {
  description = "Target region."
  type        = string
  default     = "us-central1"
}

variable "name_prefix" {
  description = "Resource name prefix."
  type        = string
  default     = "churnops"
}

variable "container_image" {
  description = "Reviewed Artifact Registry image URI."
  type        = string
  default     = null
  nullable    = true
}

variable "artifact_bucket_name" {
  description = "Globally unique bucket name selected by the future operator."
  type        = string
  default     = null
  nullable    = true
}

