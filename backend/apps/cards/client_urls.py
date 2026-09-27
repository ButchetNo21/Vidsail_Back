from django.urls import path

from apps.cards.client_views import (
    BindCardView, ClientAdListView, ClientConfigView, ClientPromptListView, PollView, RegisterDeviceView,
)

urlpatterns = [
    path('register-device', RegisterDeviceView.as_view()),
    path('bind-card', BindCardView.as_view()),
    path('poll', PollView.as_view()),
    path('prompts', ClientPromptListView.as_view()),
    path('ads', ClientAdListView.as_view()),
    path('config', ClientConfigView.as_view()),
]
