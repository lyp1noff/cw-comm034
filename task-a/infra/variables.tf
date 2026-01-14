variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "billing_account_id" {
  type      = string
  sensitive = true
}
