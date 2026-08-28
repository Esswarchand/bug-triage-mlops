variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "The environment for the deployment (e.g., dev, staging, prod)."
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "The name of the project for tagging purposes."
  type        = string
  default     = "bug-triage-mlops"
}
