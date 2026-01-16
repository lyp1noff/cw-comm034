module "bigquery_data_warehouse" {
  source = "git::https://github.com/terraform-google-modules/terraform-google-bigquery.git//modules/data_warehouse?ref=sic-jss-3"

  project_id = var.project_id
  region     = var.region
}

output "looker_studio_link" {
  value = module.bigquery_data_warehouse.lookerstudio_report_url
}

output "bigquery_console_link" {
  value = module.bigquery_data_warehouse.bigquery_editor_url
}

output "dataset_name" {
  value = module.bigquery_data_warehouse.ds_friendly_name
}

output "storage_bucket" {
  value = module.bigquery_data_warehouse.raw_bucket
}
