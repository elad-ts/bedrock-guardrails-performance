#------------------------------------------------------------------------------
# AWS Bedrock Guardrail Module
# A comprehensive guardrail configuration for Amazon Bedrock
#------------------------------------------------------------------------------

resource "aws_bedrock_guardrail" "this" {
  name                      = var.guardrail_name
  description               = var.description
  blocked_input_messaging   = var.blocked_input_messaging
  blocked_outputs_messaging = var.blocked_outputs_messaging

  #----------------------------------------------------------------------------
  # Content Policy Configuration
  # Filters for harmful content categories
  #----------------------------------------------------------------------------
  dynamic "content_policy_config" {
    for_each = var.enable_content_policy ? [1] : []
    content {
      dynamic "filters_config" {
        for_each = var.content_filters
        content {
          type            = filters_config.value.type
          input_strength  = filters_config.value.input_strength
          output_strength = filters_config.value.output_strength
        }
      }
    }
  }

  #----------------------------------------------------------------------------
  # Sensitive Information Policy Configuration
  # PII detection and redaction
  #----------------------------------------------------------------------------
  dynamic "sensitive_information_policy_config" {
    for_each = var.enable_sensitive_info_policy ? [1] : []
    content {
      # PII Entity Types
      dynamic "pii_entities_config" {
        for_each = var.pii_entities
        content {
          type   = pii_entities_config.value.type
          action = pii_entities_config.value.action
        }
      }

      # Custom Regex Patterns
      dynamic "regexes_config" {
        for_each = var.custom_regex_patterns
        content {
          name        = regexes_config.value.name
          description = regexes_config.value.description
          pattern     = regexes_config.value.pattern
          action      = regexes_config.value.action
        }
      }
    }
  }

  #----------------------------------------------------------------------------
  # Topic Policy Configuration
  # Block specific topics from being discussed
  #----------------------------------------------------------------------------
  dynamic "topic_policy_config" {
    for_each = var.enable_topic_policy ? [1] : []
    content {
      dynamic "topics_config" {
        for_each = var.denied_topics
        content {
          name       = topics_config.value.name
          definition = topics_config.value.definition
          type       = "DENY"
          examples   = topics_config.value.examples != null ? topics_config.value.examples : []
        }
      }
    }
  }

  #----------------------------------------------------------------------------
  # Word Policy Configuration
  # Block specific words, phrases, and profanity
  #----------------------------------------------------------------------------
  dynamic "word_policy_config" {
    for_each = var.enable_word_policy ? [1] : []
    content {
      # Managed word lists (profanity filter)
      dynamic "managed_word_lists_config" {
        for_each = var.enable_profanity_filter ? [1] : []
        content {
          type = "PROFANITY"
        }
      }

      # Custom blocked words
      dynamic "words_config" {
        for_each = var.blocked_words
        content {
          text = words_config.value
        }
      }
    }
  }

  #----------------------------------------------------------------------------
  # Contextual Grounding Policy Configuration
  # Ensure responses are grounded in provided context
  #----------------------------------------------------------------------------
  dynamic "contextual_grounding_policy_config" {
    for_each = var.enable_contextual_grounding ? [1] : []
    content {
      dynamic "filters_config" {
        for_each = var.contextual_grounding_filters
        content {
          type      = filters_config.value.type
          threshold = filters_config.value.threshold
        }
      }
    }
  }

  tags = var.tags
}

#------------------------------------------------------------------------------
# Guardrail Version
# Create a versioned snapshot of the guardrail
#------------------------------------------------------------------------------
resource "aws_bedrock_guardrail_version" "this" {
  count = var.create_version ? 1 : 0

  guardrail_arn = aws_bedrock_guardrail.this.guardrail_arn
  description   = var.version_description

  depends_on = [aws_bedrock_guardrail.this]
}
