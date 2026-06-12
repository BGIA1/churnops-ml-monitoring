locals {
  resource_count = var.enable_deployment ? 1 : 0
}

resource "google_artifact_registry_repository" "containers" {
  count         = local.resource_count
  location      = var.region
  repository_id = "${var.name_prefix}-containers"
  format        = "DOCKER"
  description   = "ChurnOps reviewed container images"
}

resource "google_storage_bucket" "artifacts" {
  count                       = local.resource_count
  name                        = var.artifact_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_secret_manager_secret" "runtime" {
  count     = local.resource_count
  secret_id = "${var.name_prefix}-runtime"
  replication {
    auto {}
  }
}

resource "google_cloud_run_v2_service" "api" {
  count    = local.resource_count
  name     = "${var.name_prefix}-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
    containers {
      image = var.container_image
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }
}

resource "google_cloud_run_v2_job" "operations" {
  count    = local.resource_count
  name     = "${var.name_prefix}-operations"
  location = var.region

  template {
    template {
      max_retries = 1
      timeout     = "900s"
      containers {
        image   = var.container_image
        command = ["churnops"]
        args    = ["monitor-drift"]
      }
    }
  }
}

