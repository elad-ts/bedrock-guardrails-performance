# Bedrock Guardrails Performance Benchmark

Benchmarking Amazon Bedrock Guardrails to measure the performance impact of adding safety policies to your generative AI applications.

## Overview

This repository contains:

- **Terraform modules** for deploying Bedrock Guardrails with configurable policies
- **Benchmark scripts** for measuring latency overhead
- **Example configurations** for both enterprise and minimal guardrail setups

## Key Findings

| Method | Mean Latency | Overhead |
|--------|--------------|----------|
| No Protection (Baseline) | ~1,667 ms | — |
| Bedrock Guardrail | ~2,192 ms | +525 ms (+31.5%) |
| Python Regex | ~1,478 ms | +0.4 ms (~0%) |

**But** - regex-based detection misses obfuscated PII like:
- `john dot doe at example dot com` (email)
- `one two three, four five, six seven eight nine` (SSN)

Guardrails use ML models that understand semantic meaning and catch these edge cases.

## Project Structure

```
.
├── modules/
│   └── bedrock-guardrail/     # Reusable Terraform module
├── examples/
│   ├── complete/              # Full enterprise guardrail config
│   ├── simple-pii/            # Minimal PII-only guardrail
│   └── minimal/               # Bare minimum setup
├── benchmark.py               # Full guardrail benchmark script
├── benchmark_pii_comparison.py # PII detection comparison (guardrail vs regex)
└── requirements.txt
```

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform >= 1.0
- Python 3.9+
- boto3

### Deploy a Guardrail

```bash
cd examples/simple-pii
terraform init
terraform apply
```

### Run Benchmarks

```bash
pip install -r requirements.txt

# Full guardrail benchmark
python benchmark.py

# PII detection comparison (guardrail vs regex)
python benchmark_pii_comparison.py
```

## Guardrail Configurations

### Simple PII Guardrail

Minimal configuration with 3 PII types:
- Email (anonymize)
- Phone (anonymize)
- SSN (block)

### Complete Enterprise Guardrail

Full configuration with:
- Content filters (hate, violence, sexual, misconduct, prompt attacks)
- PII detection (14 entity types)
- Topic policies with examples
- Profanity filter
- Contextual grounding
- Custom regex patterns

## Terraform Module Usage

```hcl
module "bedrock_guardrail" {
  source = "./modules/bedrock-guardrail"

  guardrail_name = "my-guardrail"
  description    = "Production guardrail"

  enable_content_policy        = true
  enable_sensitive_info_policy = true
  enable_topic_policy          = true
  enable_word_policy           = true
  enable_contextual_grounding  = true

  pii_entities = [
    { type = "EMAIL", action = "ANONYMIZE" },
    { type = "PHONE", action = "ANONYMIZE" },
    { type = "US_SOCIAL_SECURITY_NUMBER", action = "BLOCK" }
  ]

  create_version = true
}
```

## Resources

- [Amazon Bedrock Guardrails Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html)
- [Terraform AWS Provider - Bedrock Guardrail](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/bedrock_guardrail)
- [ApplyGuardrail API](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-independent-api.html)

## License

MIT
