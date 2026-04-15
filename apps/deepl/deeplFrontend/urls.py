# SPDX-License-Identifier: Apache-2.0
from django.urls import path
from . import views

urlpatterns = [
    path("", views.deepl_translation),
    path("translation/", views.deepl_translation, name="translation-form"),
    path("translation/document/", views.deepl_document_translation, name="document-translation"),
    path("translation/document/<uuid:job_id>/status/", views.deepl_document_job_status, name="document-job-status"),
    path("translation/document/<uuid:job_id>/download/", views.deepl_document_download, name="document-download"),
    path("beta/deactivate/", views.deactivate_beta, name="deactivate-beta"),
    path("stat/<slug:granularity>", views.deepl_daily_statistics, name="usage-statistics"),
]
