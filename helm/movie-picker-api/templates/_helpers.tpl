{{- define "movie-picker-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "movie-picker-api.fullname" -}}
{{- default (include "movie-picker-api.name" .) .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "movie-picker-api.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/name: {{ include "movie-picker-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app: movie-picker-api
{{- end }}

{{- define "movie-picker-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "movie-picker-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app: movie-picker-api
{{- end }}
