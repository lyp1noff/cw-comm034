
module "bigquery_data_warehouse" {
  source = "git::https://github.com/terraform-google-modules/terraform-google-bigquery.git//modules/data_warehouse?ref=sic-jss-3"

  project_id = var.project_id
  region     = var.region
}
