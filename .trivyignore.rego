# METADATA
# description: Trivy reports vulnerabilities from pip embedded CycloneDX SBOM instead of installed Python packages
# related_resources:
# - ref: https://github.com/aquasecurity/trivy/discussions/11031
package trivy

default ignore = false

ignore {
    input.VulnerabilityID == "CVE-2025-47273"
    input.PkgIdentifier.BOMRef == "pkg:pypi/setuptools@70.3.0"
}

ignore {
    input.VulnerabilityID == "GHSA-6v7p-g79w-8964"
    input.PkgIdentifier.BOMRef == "pkg:pypi/msgpack@1.1.2"
}
