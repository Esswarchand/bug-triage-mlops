output "ecr_repository_url" {
  value       = aws_ecr_repository.api_repo.repository_url
  description = "AWS ECR Repository URL"
}

output "eks_cluster_name" {
  value       = module.eks.cluster_name
  description = "EKS Cluster Name"
}

output "eks_cluster_endpoint" {
  value       = module.eks.cluster_endpoint
  description = "EKS Control Plane Endpoint"
}

output "opensearch_endpoint" {
  value       = aws_opensearch_domain.bug_search.endpoint
  description = "AWS OpenSearch Domain HTTPS Endpoint"
}