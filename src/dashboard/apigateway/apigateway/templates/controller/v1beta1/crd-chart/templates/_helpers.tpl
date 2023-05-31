{{/*
Expand the name of the chart.
*/}}
{{- define "bk-gateway-release.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 32 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "bk-gateway-release.fullname" -}}
{{- $name := default .Chart.Name .Values.apiName }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 32 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 32 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "bk-gateway-release.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "bk-gateway-release.labels" -}}
helm.sh/chart: {{ include "bk-gateway-release.chart" . }}
{{ include "bk-gateway-release.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "bk-gateway-release.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bk-gateway-release.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}