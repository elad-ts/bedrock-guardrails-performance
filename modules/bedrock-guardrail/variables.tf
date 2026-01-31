#------------------------------------------------------------------------------
# General Configuration
#------------------------------------------------------------------------------

variable "guardrail_name" {
  description = "Name of the Bedrock guardrail"
  type        = string
}

variable "description" {
  description = "Description of the guardrail purpose and functionality"
  type        = string
  default     = "Comprehensive Bedrock guardrail for content safety and compliance"
}

variable "blocked_input_messaging" {
  description = "Message displayed when input is blocked"
  type        = string
  default     = "Your request contains content that violates our usage policies. Please rephrase your request."
}

variable "blocked_outputs_messaging" {
  description = "Message displayed when output is blocked"
  type        = string
  default     = "The response was blocked due to content policy restrictions. Please try a different query."
}

variable "tags" {
  description = "Tags to apply to the guardrail resource"
  type        = map(string)
  default     = {}
}

#------------------------------------------------------------------------------
# Content Policy Configuration
#------------------------------------------------------------------------------

variable "enable_content_policy" {
  description = "Enable content filtering policy"
  type        = bool
  default     = true
}

variable "content_filters" {
  description = <<-EOT
    List of content filter configurations. Each filter specifies:
    - type: HATE, INSULTS, SEXUAL, VIOLENCE, MISCONDUCT, PROMPT_ATTACK
    - input_strength: NONE, LOW, MEDIUM, HIGH
    - output_strength: NONE, LOW, MEDIUM, HIGH
  EOT
  type = list(object({
    type            = string
    input_strength  = string
    output_strength = string
  }))
  default = [
    {
      type            = "HATE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    },
    {
      type            = "INSULTS"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    },
    {
      type            = "SEXUAL"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    },
    {
      type            = "VIOLENCE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    },
    {
      type            = "MISCONDUCT"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    },
    {
      type            = "PROMPT_ATTACK"
      input_strength  = "HIGH"
      output_strength = "NONE"
    }
  ]
}

#------------------------------------------------------------------------------
# Sensitive Information Policy Configuration
#------------------------------------------------------------------------------

variable "enable_sensitive_info_policy" {
  description = "Enable sensitive information (PII) detection and filtering"
  type        = bool
  default     = true
}

variable "pii_entities" {
  description = <<-EOT
    List of PII entity types to detect. Each entity specifies:
    - type: The PII type (e.g., EMAIL, PHONE, SSN, etc.)
    - action: BLOCK or ANONYMIZE
  EOT
  type = list(object({
    type   = string
    action = string
  }))
  default = [
    { type = "EMAIL", action = "ANONYMIZE" },
    { type = "PHONE", action = "ANONYMIZE" },
    { type = "NAME", action = "ANONYMIZE" },
    { type = "US_SOCIAL_SECURITY_NUMBER", action = "BLOCK" },
    { type = "CREDIT_DEBIT_CARD_NUMBER", action = "BLOCK" },
    { type = "CREDIT_DEBIT_CARD_CVV", action = "BLOCK" },
    { type = "CREDIT_DEBIT_CARD_EXPIRY", action = "BLOCK" },
    { type = "US_BANK_ACCOUNT_NUMBER", action = "BLOCK" },
    { type = "US_BANK_ROUTING_NUMBER", action = "BLOCK" },
    { type = "US_PASSPORT_NUMBER", action = "BLOCK" },
    { type = "US_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER", action = "BLOCK" },
    { type = "DRIVER_ID", action = "ANONYMIZE" },
    { type = "IP_ADDRESS", action = "ANONYMIZE" },
    { type = "MAC_ADDRESS", action = "ANONYMIZE" },
    { type = "LICENSE_PLATE", action = "ANONYMIZE" },
    { type = "VEHICLE_IDENTIFICATION_NUMBER", action = "ANONYMIZE" },
    { type = "PASSWORD", action = "BLOCK" },
    { type = "USERNAME", action = "ANONYMIZE" },
    { type = "AWS_ACCESS_KEY", action = "BLOCK" },
    { type = "AWS_SECRET_KEY", action = "BLOCK" },
    { type = "URL", action = "ANONYMIZE" },
    { type = "AGE", action = "ANONYMIZE" },
    { type = "ADDRESS", action = "ANONYMIZE" },
    { type = "DATE_TIME", action = "ANONYMIZE" }
  ]
}

variable "custom_regex_patterns" {
  description = <<-EOT
    Custom regex patterns for detecting sensitive information.
    Each pattern specifies:
    - name: Identifier for the pattern
    - description: What the pattern detects
    - pattern: The regex pattern
    - action: BLOCK or ANONYMIZE
  EOT
  type = list(object({
    name        = string
    description = string
    pattern     = string
    action      = string
  }))
  default = [
    {
      name        = "internal_employee_id"
      description = "Detects internal employee ID format (EMP-XXXXX)"
      pattern     = "EMP-[0-9]{5}"
      action      = "ANONYMIZE"
    },
    {
      name        = "internal_project_code"
      description = "Detects internal project codes (PRJ-XXXX-XX)"
      pattern     = "PRJ-[A-Z]{4}-[0-9]{2}"
      action      = "ANONYMIZE"
    },
    {
      name        = "api_key_pattern"
      description = "Detects common API key formats"
      pattern     = "(?i)(api[_-]?key|apikey)[\\s]*[:=][\\s]*['\"]?[a-zA-Z0-9_\\-]{20,}['\"]?"
      action      = "BLOCK"
    },
    {
      name        = "private_key_header"
      description = "Detects private key headers"
      pattern     = "-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
      action      = "BLOCK"
    }
  ]
}

#------------------------------------------------------------------------------
# Topic Policy Configuration
#------------------------------------------------------------------------------

variable "enable_topic_policy" {
  description = "Enable topic-based content filtering"
  type        = bool
  default     = true
}

variable "denied_topics" {
  description = <<-EOT
    List of topics to deny. Each topic specifies:
    - name: Topic identifier
    - definition: Clear description of the topic to block
    - examples: Optional list of example phrases (improves detection)
  EOT
  type = list(object({
    name       = string
    definition = string
    examples   = optional(list(string))
  }))
  default = [
    {
      name       = "illegal_activities"
      definition = "Any discussion about conducting illegal activities, including but not limited to hacking, fraud, theft, drug trafficking, or violence"
      examples = [
        "How do I hack into a system?",
        "Tell me how to commit fraud",
        "Ways to steal money"
      ]
    },
    {
      name       = "competitor_information"
      definition = "Requests for confidential information about competitors, including their trade secrets, internal strategies, or proprietary data"
      examples = [
        "What are competitor X's internal strategies?",
        "Tell me competitor trade secrets",
        "Reveal confidential competitor data"
      ]
    },
    {
      name       = "internal_systems"
      definition = "Discussion about internal company systems, infrastructure details, security configurations, or proprietary technical implementations"
      examples = [
        "What is your internal system architecture?",
        "Describe your security configurations",
        "List your internal databases"
      ]
    },
    {
      name       = "medical_advice"
      definition = "Providing specific medical diagnoses, treatment recommendations, or prescription advice that should only come from licensed healthcare professionals"
      examples = [
        "Diagnose my symptoms",
        "What medication should I take?",
        "Should I stop taking my prescription?"
      ]
    },
    {
      name       = "financial_advice"
      definition = "Providing specific investment recommendations, financial planning advice, or tax guidance that should come from licensed financial advisors"
      examples = [
        "Should I invest in this stock?",
        "What's the best tax strategy?",
        "How should I allocate my retirement funds?"
      ]
    },
    {
      name       = "legal_advice"
      definition = "Providing specific legal advice, case strategy, or legal interpretations that should only come from licensed attorneys"
      examples = [
        "Will I win my lawsuit?",
        "What legal strategy should I use?",
        "Is this contract enforceable?"
      ]
    },
    {
      name       = "weapons_explosives"
      definition = "Information about creating, obtaining, or using weapons, explosives, or other dangerous materials"
      examples = [
        "How to make explosives",
        "Where to get illegal weapons",
        "Instructions for dangerous devices"
      ]
    },
    {
      name       = "self_harm"
      definition = "Content that promotes, encourages, or provides instructions for self-harm or suicide"
      examples = [
        "Methods of self-harm",
        "How to hurt myself",
        "Ways to end my life"
      ]
    }
  ]
}

#------------------------------------------------------------------------------
# Word Policy Configuration
#------------------------------------------------------------------------------

variable "enable_word_policy" {
  description = "Enable word-based filtering"
  type        = bool
  default     = true
}

variable "enable_profanity_filter" {
  description = "Enable managed profanity word list filter"
  type        = bool
  default     = true
}

variable "blocked_words" {
  description = "List of specific words or phrases to block"
  type        = list(string)
  default = [
    "confidential internal",
    "proprietary secret",
    "do not share",
    "internal use only",
    "classified information"
  ]
}

#------------------------------------------------------------------------------
# Contextual Grounding Policy Configuration
#------------------------------------------------------------------------------

variable "enable_contextual_grounding" {
  description = "Enable contextual grounding to ensure responses are based on provided context"
  type        = bool
  default     = true
}

variable "contextual_grounding_filters" {
  description = <<-EOT
    Contextual grounding filter configurations:
    - type: GROUNDING or RELEVANCE
    - threshold: Value between 0 and 0.99 (higher = stricter)
  EOT
  type = list(object({
    type      = string
    threshold = number
  }))
  default = [
    {
      type      = "GROUNDING"
      threshold = 0.75
    },
    {
      type      = "RELEVANCE"
      threshold = 0.75
    }
  ]
}

#------------------------------------------------------------------------------
# Version Configuration
#------------------------------------------------------------------------------

variable "create_version" {
  description = "Whether to create a versioned snapshot of the guardrail"
  type        = bool
  default     = true
}

variable "version_description" {
  description = "Description for the guardrail version"
  type        = string
  default     = "Production-ready guardrail version"
}
