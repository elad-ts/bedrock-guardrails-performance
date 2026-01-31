#------------------------------------------------------------------------------
# Example: Complete Bedrock Guardrail Configuration
#------------------------------------------------------------------------------

provider "aws" {
  region = "us-east-1"
}

module "bedrock_guardrail" {
  source = "../../modules/bedrock-guardrail"

  guardrail_name = "comprehensive-enterprise-guardrail"
  description    = "Enterprise-grade guardrail with full content safety, PII protection, and topic filtering"

  blocked_input_messaging   = "Your request has been blocked due to policy violations. Please revise your input and try again."
  blocked_outputs_messaging = "The generated response was blocked due to content policy restrictions. Please modify your query."

  # Content Policy - All categories enabled with HIGH filtering
  enable_content_policy = true
  content_filters = [
    { type = "HATE", input_strength = "HIGH", output_strength = "HIGH" },
    { type = "INSULTS", input_strength = "HIGH", output_strength = "HIGH" },
    { type = "SEXUAL", input_strength = "HIGH", output_strength = "HIGH" },
    { type = "VIOLENCE", input_strength = "HIGH", output_strength = "HIGH" },
    { type = "MISCONDUCT", input_strength = "HIGH", output_strength = "HIGH" },
    { type = "PROMPT_ATTACK", input_strength = "HIGH", output_strength = "NONE" }
  ]

  # Sensitive Information Policy - Comprehensive PII protection
  enable_sensitive_info_policy = true
  pii_entities = [
    { type = "EMAIL", action = "ANONYMIZE" },
    { type = "PHONE", action = "ANONYMIZE" },
    { type = "NAME", action = "ANONYMIZE" },
    { type = "US_SOCIAL_SECURITY_NUMBER", action = "BLOCK" },
    { type = "CREDIT_DEBIT_CARD_NUMBER", action = "BLOCK" },
    { type = "CREDIT_DEBIT_CARD_CVV", action = "BLOCK" },
    { type = "CREDIT_DEBIT_CARD_EXPIRY", action = "BLOCK" },
    { type = "US_BANK_ACCOUNT_NUMBER", action = "BLOCK" },
    { type = "US_BANK_ROUTING_NUMBER", action = "BLOCK" },
    { type = "PASSWORD", action = "BLOCK" },
    { type = "AWS_ACCESS_KEY", action = "BLOCK" },
    { type = "AWS_SECRET_KEY", action = "BLOCK" },
    { type = "IP_ADDRESS", action = "ANONYMIZE" },
    { type = "ADDRESS", action = "ANONYMIZE" }
  ]

  # Custom regex patterns for organization-specific sensitive data
  custom_regex_patterns = [
    {
      name        = "internal_employee_id"
      description = "Detects internal employee ID format"
      pattern     = "EMP-[0-9]{5}"
      action      = "ANONYMIZE"
    },
    {
      name        = "api_key_generic"
      description = "Detects generic API key patterns"
      pattern     = "(?i)(api[_-]?key|apikey)[\\s]*[:=][\\s]*['\"]?[a-zA-Z0-9_\\-]{20,}['\"]?"
      action      = "BLOCK"
    }
  ]

  # Topic Policy - Block sensitive discussion topics
  enable_topic_policy = true
  denied_topics = [
    {
      name       = "illegal_activities"
      definition = "Any discussion about conducting illegal activities"
      examples   = ["How do I hack?", "Ways to commit fraud"]
    },
    {
      name       = "competitor_secrets"
      definition = "Requests for confidential competitor information"
      examples   = ["What are competitor trade secrets?"]
    },
    {
      name       = "medical_diagnosis"
      definition = "Providing medical diagnoses or treatment recommendations"
      examples   = ["Diagnose my condition", "What medication should I take?"]
    }
  ]

  # Word Policy - Block specific terms
  enable_word_policy      = true
  enable_profanity_filter = true
  blocked_words = [
    "confidential internal",
    "proprietary secret",
    "do not distribute"
  ]

  # Contextual Grounding - Ensure factual responses
  enable_contextual_grounding = true
  contextual_grounding_filters = [
    { type = "GROUNDING", threshold = 0.75 },
    { type = "RELEVANCE", threshold = 0.75 }
  ]

  # Version the guardrail for production use
  create_version      = true
  version_description = "v1.0.0 - Initial production release"

  tags = {
    Environment = "production"
    Team        = "platform"
    ManagedBy   = "terraform"
  }
}

#------------------------------------------------------------------------------
# Outputs
#------------------------------------------------------------------------------

output "guardrail_id" {
  value = module.bedrock_guardrail.guardrail_id
}

output "guardrail_arn" {
  value = module.bedrock_guardrail.guardrail_arn
}

output "guardrail_version" {
  value = module.bedrock_guardrail.version_number
}
