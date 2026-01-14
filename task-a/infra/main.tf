locals {
  project_id = var.project_id
  region     = var.region
  compute_sa = "${data.google_project.project_details.number}-compute@developer.gserviceaccount.com"
  image_name = "${local.region}-docker.pkg.dev/${local.project_id}/${google_artifact_registry_repository.api_repo.repository_id}/flask-app:latest"
}

resource "google_project" "project" {
  name            = "CW Task A Terraform"
  project_id      = local.project_id
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
    "eventarc.googleapis.com",
    "pubsub.googleapis.com",
    "iamcredentials.googleapis.com"
  ])
  project            = google_project.project.project_id
  service            = each.key
  disable_on_destroy = false
}

resource "time_sleep" "wait_for_services" {
  depends_on      = [google_project_service.services]
  create_duration = "60s"
}

resource "google_storage_bucket" "buckets" {
  for_each      = toset(["in", "out", "source"])
  name          = "${local.project_id}-${each.key}"
  location      = local.region
  project       = google_project.project.project_id
  force_destroy = true
}

data "google_storage_project_service_account" "gcs_account" {
  project    = google_project.project.project_id
  depends_on = [time_sleep.wait_for_services]
}

resource "google_project_iam_member" "permissions" {
  for_each = {
    "gcs_pubsub"     = "roles/pubsub.publisher",
    "event_receiver" = "roles/eventarc.eventReceiver",
    "token_creator"  = "roles/iam.serviceAccountTokenCreator"
  }
  project = google_project.project.project_id
  role    = each.value
  member  = each.key == "gcs_pubsub" ? "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}" : "serviceAccount:${local.compute_sa}"
}

resource "google_storage_bucket_iam_member" "bucket_access" {
  bucket     = google_storage_bucket.buckets["in"].name
  role       = "roles/storage.objectViewer"
  member     = "serviceAccount:${local.compute_sa}"
  depends_on = [time_sleep.wait_for_services]
}

resource "google_storage_bucket_iam_member" "bucket_output_access" {
  bucket     = google_storage_bucket.buckets["out"].name
  role       = "roles/storage.objectCreator"
  member     = "serviceAccount:${local.compute_sa}"
  depends_on = [time_sleep.wait_for_services]
}

resource "google_storage_bucket_iam_member" "bucket_output_public_access" {
  bucket = google_storage_bucket.buckets["out"].name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

data "archive_file" "function_zip" {
  type        = "zip"
  output_path = "${path.module}/text_processor.zip"
  source_dir  = "${path.module}/../text_processor"
}

resource "google_storage_bucket_object" "function_source" {
  name   = "source.${data.archive_file.function_zip.output_md5}.zip"
  bucket = google_storage_bucket.buckets["source"].name
  source = data.archive_file.function_zip.output_path
}

resource "google_cloudfunctions2_function" "file_analyzer" {
  name     = "file-analyzer"
  project  = google_project.project.project_id
  location = local.region

  build_config {
    runtime     = "python312"
    entry_point = "process_file"
    source {
      storage_source {
        bucket = google_storage_bucket.buckets["source"].name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count = 10
    available_memory   = "256M"
    environment_variables = {
      OUTPUT_BUCKET = google_storage_bucket.buckets["out"].name
    }
  }

  event_trigger {
    trigger_region = local.region
    event_type     = "google.cloud.storage.object.v1.finalized"
    retry_policy   = "RETRY_POLICY_RETRY"
    event_filters {
      attribute = "bucket"
      value     = google_storage_bucket.buckets["in"].name
    }
  }

  depends_on = [time_sleep.wait_for_services]
}

resource "google_artifact_registry_repository" "api_repo" {
  project       = google_project.project.project_id
  location      = local.region
  repository_id = "flask-api-repo"
  format        = "DOCKER"
  depends_on    = [time_sleep.wait_for_services]
}

resource "null_resource" "build_flask_image" {
  triggers = {
    dir_hash = sha1(join("", [for f in fileset("${path.module}/../flask", "**") : filesha1("${path.module}/../flask/${f}")]))
  }

  provisioner "local-exec" {
    command = <<EOT
      gcloud builds submit --project ${google_project.project.project_id} \
        --tag ${local.image_name} \
        ${path.module}/../flask/
    EOT
  }

  depends_on = [google_artifact_registry_repository.api_repo]
}

resource "google_cloud_run_v2_service" "flask_api" {
  name     = "flask-api"
  location = local.region
  project  = google_project.project.project_id

  invoker_iam_disabled = true

  template {
    containers {
      image = local.image_name
      env {
        name  = "BUCKET_IN"
        value = google_storage_bucket.buckets["in"].name
      }
      env {
        name  = "BUCKET_OUT"
        value = google_storage_bucket.buckets["out"].name
      }
    }
  }

  lifecycle {
    ignore_changes = [
      client,
      client_version,
      template[0].containers[0].name
    ]
  }

  depends_on = [null_resource.build_flask_image]
}
