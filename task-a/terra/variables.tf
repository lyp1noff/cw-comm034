variable "project_id" {
  type    = string
  default = "cw-a-terra-484220"
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "billing_account_id" {
  type      = string
  sensitive = true
}
