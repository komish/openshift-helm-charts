{{/*
truncates the chart name if necessary
*/}}
{{- define "hc-minimal.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
App Name
*/}}
{{- define "hc-minimal.fullname" -}}
{{- printf "%s-%s" .Release.Name "helmcert" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "hc-minimal.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "hc-minimal.labels" -}}
helm.sh/chart: {{ include "hc-minimal.chart" . }}
{{ include "hc-minimal.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "hc-minimal.selectorLabels" -}}
app.kubernetes.io/name: {{ include "hc-minimal.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "hc-minimal.serviceAccountName" -}}
{{- printf "%s-%s" .Release.Name "sa" | trunc 63 | trimSuffix "-" }}
{{- end }}