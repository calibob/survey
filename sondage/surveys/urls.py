from django.urls import path
from . import views

app_name = 'surveys'

urlpatterns = [
    # Vue d'accueil
    path('', views.HomeView.as_view(), name='home'),
    
    # Tableau de bord administrateur
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/export/', views.DashboardExportView.as_view(), name='dashboard_export'),
    path('dashboard/archive/', views.BulkArchiveSurveyView.as_view(), name='bulk_archive'),
    
    # Gestion des sondages
    path('surveys/', views.SurveyListView.as_view(), name='survey_list'),
    path('surveys/create/', views.SurveyCreateView.as_view(), name='survey_create'),
    path('surveys/<int:pk>/', views.SurveyDetailView.as_view(), name='survey_detail'),
    path('surveys/<int:pk>/update/', views.SurveyUpdateView.as_view(), name='survey_update'),
    path('surveys/<int:pk>/delete/', views.SurveyDeleteView.as_view(), name='survey_delete'),
    path('surveys/<int:pk>/preview/', views.SurveyPreviewView.as_view(), name='survey_preview'),
    path('surveys/<int:pk>/export/', views.SurveyExportView.as_view(), name='survey_export'),
    path('surveys/<int:pk>/results/', views.SurveyResultsView.as_view(), name='survey_results'),
    path('surveys/<int:pk>/archive/', views.ArchiveSurveyView.as_view(), name='survey_archive'),
    
    # Gestion des questions
    path('surveys/<int:survey_id>/question/add/', views.question_create_view, name='question_add'),
    path('question/<int:pk>/update/', views.question_update_view, name='question_update'),
    
    # Gestion des sauts de page
    path('surveys/<int:survey_id>/pagebreak/add/', views.PageBreakCreateView.as_view(), name='pagebreak_add'),
    path('pagebreak/<int:pk>/update/', views.PageBreakUpdateView.as_view(), name='pagebreak_update'),
    path('pagebreak/<int:pk>/delete/', views.PageBreakDeleteView.as_view(), name='pagebreak_delete'),
    
    # Gestion des thèmes
    path('themes/', views.SurveyThemeListView.as_view(), name='theme_list'),
    path('themes/create/', views.SurveyThemeCreateView.as_view(), name='theme_create'),
    path('themes/<int:pk>/update/', views.SurveyThemeUpdateView.as_view(), name='theme_update'),
    path('themes/<int:pk>/delete/', views.SurveyThemeDeleteView.as_view(), name='theme_delete'),
    
    # Participation aux sondages
    path('surveys/<int:pk>/respond/', views.SurveyResponseView.as_view(), name='survey_respond'),
    path('surveys/respond/<str:token>/', views.SurveyResponsePrivateView.as_view(), name='survey_respond_private'),
    path('surveys/<int:pk>/password/', views.SurveyPasswordView.as_view(), name='survey_password'),
    path('surveys/password/<str:token>/', views.SurveyPasswordView.as_view(), name='survey_password_token'),
    path('surveys/<int:pk>/thankyou/', views.SurveyThankYouView.as_view(), name='survey_thankyou'),
]
