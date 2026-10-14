{{- define "medislot.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 50 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 50 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "medislot.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/part-of: medislot
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/* Selector labels for one component: include "medislot.selectorLabels" (list . "backend") */}}
{{- define "medislot.selectorLabels" -}}
{{- $root := index . 0 -}}
app.kubernetes.io/name: {{ printf "medislot-%s" (index . 1) }}
app.kubernetes.io/instance: {{ $root.Release.Name }}
{{- end -}}

{{- define "medislot.componentLabels" -}}
{{ include "medislot.labels" (index . 0) }}
{{ include "medislot.selectorLabels" . }}
app.kubernetes.io/component: {{ index . 1 }}
{{- end -}}

{{- define "medislot.image" -}}
{{- $root := index . 0 -}}
{{- $img := index . 1 -}}
{{- printf "%s:%s" $img.repository (default $root.Chart.AppVersion $img.tag | toString) -}}
{{- end -}}

{{- define "medislot.backendService" -}}{{ include "medislot.fullname" . }}-backend{{- end -}}
{{- define "medislot.frontendService" -}}{{ include "medislot.fullname" . }}-frontend{{- end -}}
{{- define "medislot.postgresService" -}}{{ include "medislot.fullname" . }}-postgres{{- end -}}
{{- define "medislot.secretName" -}}{{ include "medislot.fullname" . }}-db{{- end -}}

{{- define "medislot.dbHost" -}}
{{- if .Values.postgres.enabled -}}
{{ include "medislot.postgresService" . }}
{{- else -}}
{{ required "postgres.externalHost is required when postgres.enabled=false" .Values.postgres.externalHost }}
{{- end -}}
{{- end -}}

{{- define "medislot.podSecurityContext" -}}
runAsNonRoot: true
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "medislot.containerSecurityContext" -}}
allowPrivilegeEscalation: false
capabilities:
  drop: ["ALL"]
{{- end -}}
