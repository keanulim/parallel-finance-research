variable "region" {
  type    = string
  default = "us-east-1"
}

variable "state_bucket_name" {
  type        = string
  description = "Must be globally unique across all of AWS, not just your account."
}

variable "lock_table_name" {
  type    = string
  default = "finance-agents-terraform-locks"
}
