# ─────────────────────────────────────────────────────────────────────────────
# Local values — DRY resource naming and tagging
#
# All resources use consistent naming: {project}-{resource}-{environment}
# All resources share the same tag set via local.common_tags.
# ─────────────────────────────────────────────────────────────────────────────

locals {
  # Consistent naming convention for all resources
  name_prefix = "${var.project_name}-${var.environment}"

  # ACR names must be alphanumeric (no hyphens), globally unique
  acr_name = replace("${var.project_name}acr${var.environment}", "-", "")

  # Common tags applied to every resource
  common_tags = {
    Project     = "Production-GenAI-MLOps-Platform"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Repository  = "TechySan031/Production-GenAI-MLOps-Platform"
  }
}
