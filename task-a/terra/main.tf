resource "google_project" "project" {
  name            = "CW Task A Terraform"
  project_id      = var.project_id
  billing_account = var.billing_account_id
  deletion_policy = "DELETE"
}

data "google_project" "project_details" {
  project_id = google_project.project.project_id
}

resource "google_project_service" "services" {
  for_each = toset([
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "storage.googleapis.com",
  ])
  project = google_project.project.project_id
  service = each.key

  disable_on_destroy = false
}

resource "google_storage_bucket" "bucket-in" {
  name          = "${google_project.project.project_id}-in"
  location      = var.region
  project       = google_project.project.project_id
  force_destroy = true
}

resource "google_storage_bucket" "bucket-out" {
  name          = "${google_project.project.project_id}-out"
  location      = var.region
  project       = google_project.project.project_id
  force_destroy = true
}

resource "google_storage_bucket_iam_member" "invoker_in" {
  bucket = google_storage_bucket.bucket-in.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${data.google_project.project_details.number}-compute@developer.gserviceaccount.com"
}

resource "google_storage_bucket_iam_member" "invoker_out" {
  bucket = google_storage_bucket.bucket-out.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${data.google_project.project_details.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "gcs_pubsub_publishing" {
  project = google_project.project.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:service-${data.google_project.project_details.number}@gs-project-accounts.iam.gserviceaccount.com"
}

resource "google_storage_bucket" "bucket-source" {
  name          = "${google_project.project.project_id}-source"
  location      = var.region
  project       = google_project.project.project_id
  force_destroy = true
}

data "archive_file" "function_zip" {
  type        = "zip"
  output_path = "${path.module}/source_temp.zip"
  source_dir  = "${path.module}/../app"
}

resource "google_storage_bucket_object" "zip" {
  name   = "source.zip#${data.archive_file.function_zip.output_md5}"
  bucket = google_storage_bucket.bucket-source.name
  source = data.archive_file.function_zip.output_path
}

resource "google_cloudfunctions2_function" "function-file-analyzer" {
  name     = "file-analyzer"
  project  = google_project.project.project_id
  location = var.region

  build_config {
    runtime     = "python312"
    entry_point = "process_file"
    source {
      storage_source {
        bucket = google_storage_bucket.bucket-source.name
        object = google_storage_bucket_object.zip.name
      }
    }
  }

  service_config {
    max_instance_count               = 10
    min_instance_count               = 0
    max_instance_request_concurrency = 1

    available_memory = "256M"
    environment_variables = {
      OUTPUT_BUCKET = google_storage_bucket.bucket-out.name
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.storage.object.v1.finalized"
    retry_policy   = "RETRY_POLICY_RETRY"

    event_filters {
      attribute = "bucket"
      value     = google_storage_bucket.bucket-in.name
    }
  }

  depends_on = [
    google_project_service.services,
    google_storage_bucket_iam_member.invoker_in,
    google_storage_bucket_iam_member.invoker_out
  ]
}
