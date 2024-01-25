# -*- coding: utf-8 -*-
"""String templates to be used for generating various files throughout E2E testing."""

# The base OWNERS file string template.
base_owners_file: str = """\
chart:
  name: ${chart_name}
  shortDescription: Test chart for testing chart submission workflows.
publicPgpKey: ${public_key}
providerDelivery: ${provider_delivery}
users:
- githubUsername: ${bot_name}
vendor:
  label: ${vendor}
  name: ${vendor_pretty}
"""

# This is the Chart.yaml that should be auto-generated for the hc-minimal
# fixture, whenever it is used.
hc_minimal_chart_yaml: str = """\
apiVersion: v2
name: \"${chart_name}\"
description: A Helm chart for Kubernetes
type: application
version: 0.0.1
appVersion: "0.0.1"
kubeVersion: ''>= 1.14.0-0''
annotations:
  charts.openshift.io/name: "${chart_name}"
"""
