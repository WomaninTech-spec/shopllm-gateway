provider "google" {
  project = var.project_id
  region  = var.region
}
 
resource "google_artifact_registry_repository" "gateway" {
  location      = var.region
  repository_id = "shopllm-gateway"
  format        = "DOCKER"
}
 
resource "google_secret_manager_secret" "anthropic_key" {
  secret_id = "ANTHROPIC_API_KEY"
  replication {
    auto {}
  }
}
 
resource "google_service_account" "gateway_sa" {
  account_id   = "shopllm-gateway-sa"
  display_name = "ShopLLM Gateway service account"
}
 
resource "google_secret_manager_secret_iam_member" "sa_read" {
  secret_id = google_secret_manager_secret.anthropic_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.gateway_sa.email}"
}
 
resource "google_cloud_run_v2_service" "gateway" {
  name                = "shopllm-gateway"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false
 
  template {
    service_account = google_service_account.gateway_sa.email
    containers {
      image = var.image
      ports { container_port = 8000 }
      env {
        name = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.anthropic_key.secret_id
            version = "latest"
          }
        }
      }
      resources {
        limits = { cpu = "1", memory = "512Mi" }
      }
    }
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
  }
}
 
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.gateway.name
  location = google_cloud_run_v2_service.gateway.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}