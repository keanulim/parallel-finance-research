terraform {
  backend "s3" {
    bucket         = "finance-agents-tfstate-443674899565"
    key            = "vpc/terraform.tfstate"
    region         = "us-east-1" # where the state bucket itself lives
    dynamodb_table = "finance-agents-terraform-locks"
    encrypt        = true
  }
}
