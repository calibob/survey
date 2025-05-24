from django.urls import path
from . import views

app_name = 'responses'

urlpatterns = [
    path('submit/<int:survey_id>/', views.SubmitSurveyResponseView.as_view(), name='submit_response'),
    path('survey/<int:survey_id>/responses/', views.SurveyResponsesListView.as_view(), name='response_list'),
    path('response/<int:pk>/', views.SurveyResponseDetailView.as_view(), name='response_detail'),
]
