#------------------------------------------------------------------------------
# Example: Simple PII-Only Guardrail
# Minimal guardrail for performance comparison
#------------------------------------------------------------------------------

provider "aws" {
  region = "us-east-1"
}

resource "aws_bedrock_guardrail" "simple_pii" {
  name                      = "simple-pii-guardrail"
  description               = "Simple guardrail with only PII detection for performance testing"
  blocked_input_messaging   = "PII detected in input."
  blocked_outputs_messaging = "PII detected in output."

  # Only PII detection - no other filters
  sensitive_information_policy_config {
    pii_entities_config {
      type   = "EMAIL"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "PHONE"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "US_SOCIAL_SECURITY_NUMBER"
      action = "BLOCK"
    }
  }

  tags = {
    Environment = "benchmark"
    Type        = "simple-pii"
  }
}

resource "aws_bedrock_guardrail_version" "simple_pii" {
  guardrail_arn = aws_bedrock_guardrail.simple_pii.guardrail_arn
  description   = "v1.0.0 - Simple PII guardrail"
}

output "guardrail_id" {
  value = aws_bedrock_guardrail.simple_pii.guardrail_id
}

output "guardrail_arn" {
  value = aws_bedrock_guardrail.simple_pii.guardrail_arn
}

output "guardrail_version" {
  value = aws_bedrock_guardrail_version.simple_pii.version
}
