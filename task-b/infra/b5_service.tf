resource "google_service_account" "b5_app_sa" {
  project      = var.project_id
  account_id   = "b5-web-app-sa"
  display_name = "Service Account for B5 Cloud Run"
}

resource "google_project_iam_member" "bq_viewer" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.b5_app_sa.email}"
}

resource "google_project_iam_member" "bq_data_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.b5_app_sa.email}"
}

resource "google_artifact_registry_repository" "app_repo" {
  project       = var.project_id
  location      = var.region
  repository_id = "app-repo"
  format        = "DOCKER"
}

resource "google_cloud_run_v2_service" "b5_service" {
  project  = var.project_id
  location = var.region
  name     = "bq-data-portal"
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.b5_app_sa.email
    containers {
      image = "europe-west2-docker.pkg.dev/cw-b-484223-test/app-repo/b5-app:latest"
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = var.project_id
  location = google_cloud_run_v2_service.b5_service.location
  name     = google_cloud_run_v2_service.b5_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "b5_service_url" {
  value = google_cloud_run_v2_service.b5_service.uri
}
