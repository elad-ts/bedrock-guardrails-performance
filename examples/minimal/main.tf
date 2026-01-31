#------------------------------------------------------------------------------
# Example: Minimal Bedrock Guardrail Configuration
# Uses module defaults for comprehensive protection
#------------------------------------------------------------------------------

provider "aws" {
  region = "us-east-1"
}

module "bedrock_guardrail" {
  source = "../../modules/bedrock-guardrail"

  guardrail_name = "minimal-guardrail"
  description    = "Guardrail using sensible defaults"

  tags = {
    Environment = "development"
    ManagedBy   = "terraform"
  }
}

output "guardrail_arn" {
  value = module.bedrock_guardrail.guardrail_arn
}
