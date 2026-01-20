# SPDX-License-Identifier: Apache-2.0
from django.urls import path
from . import views

urlpatterns = [
    path("", views.deepl_translation),
    path("translation/", views.deepl_translation, name="translation-form"),
    path("stat/<slug:granularity>", views.deepl_daily_statistics, name="usage-statistics"),
]
