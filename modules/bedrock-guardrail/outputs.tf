#------------------------------------------------------------------------------
# Guardrail Outputs
#------------------------------------------------------------------------------

output "guardrail_id" {
  description = "The unique identifier of the guardrail"
  value       = aws_bedrock_guardrail.this.guardrail_id
}

output "guardrail_arn" {
  description = "The ARN of the guardrail"
  value       = aws_bedrock_guardrail.this.guardrail_arn
}

output "guardrail_name" {
  description = "The name of the guardrail"
  value       = aws_bedrock_guardrail.this.name
}

output "guardrail_status" {
  description = "The status of the guardrail"
  value       = aws_bedrock_guardrail.this.status
}

output "guardrail_version" {
  description = "The DRAFT version of the guardrail"
  value       = aws_bedrock_guardrail.this.version
}

output "created_at" {
  description = "Timestamp when the guardrail was created"
  value       = aws_bedrock_guardrail.this.created_at
}

#------------------------------------------------------------------------------
# Guardrail Version Outputs
#------------------------------------------------------------------------------

output "version_guardrail_arn" {
  description = "The ARN of the versioned guardrail"
  value       = var.create_version ? aws_bedrock_guardrail_version.this[0].guardrail_arn : null
}

output "version_number" {
  description = "The version number of the created guardrail version"
  value       = var.create_version ? aws_bedrock_guardrail_version.this[0].version : null
}
