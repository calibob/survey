from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib import messages

from surveys.models import Survey, Question, QuestionOption
from .models import SurveyResponse, Answer

class SubmitSurveyResponseView(View):
    """Vue pour soumettre une réponse à un sondage"""
    
    def post(self, request, *args, **kwargs):
        survey = get_object_or_404(Survey, pk=self.kwargs['survey_id'])
        
        # Créer une nouvelle réponse au sondage
        survey_response = SurveyResponse(survey=survey)
        
        # Si l'utilisateur est connecté, associer la réponse à l'utilisateur
        if request.user.is_authenticated:
            survey_response.user = request.user
        
        # Enregistrer l'adresse IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        survey_response.ip_address = ip
        
        survey_response.save()
        
        # Traiter chaque question du sondage
        questions = survey.questions.all()
        for question in questions:
            answer = Answer(survey_response=survey_response, question=question)
            
            if question.question_type == 'single':
                option_id = request.POST.get(f'question_{question.id}')
                if option_id:
                    answer.selected_option = QuestionOption.objects.get(id=option_id)
            
            elif question.question_type == 'multiple':
                # Pour les questions à choix multiples, nous stockons une seule réponse par option sélectionnée
                option_ids = request.POST.getlist(f'question_{question.id}')
                if option_ids:
                    # Pour simplifier dans cette étape 1, nous ne sauvegardons que la première option sélectionnée
                    # Dans une version future, nous traiterons correctement les choix multiples
                    answer.selected_option = QuestionOption.objects.get(id=option_ids[0])
            
            elif question.question_type == 'text':
                text_answer = request.POST.get(f'question_{question.id}')
                if text_answer:
                    answer.text_answer = text_answer
            
            elif question.question_type == 'scale':
                scale_value = request.POST.get(f'question_{question.id}')
                if scale_value:
                    answer.scale_answer = int(scale_value)
            
            answer.save()
        
        messages.success(request, 'Merci d\'avoir répondu à ce sondage !')
        return redirect('surveys:home')

class SurveyResponseDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher les détails d'une réponse à un sondage"""
    model = SurveyResponse
    template_name = 'responses/response_detail.html'
    context_object_name = 'response'
    
    def get_queryset(self):
        # S'assurer que l'utilisateur ne peut voir que les réponses des sondages qu'il a créés
        return SurveyResponse.objects.filter(survey__author=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answers'] = self.object.answers.all()
        return context

class SurveyResponsesListView(LoginRequiredMixin, ListView):
    """Vue pour lister toutes les réponses à un sondage spécifique"""
    model = SurveyResponse
    template_name = 'responses/response_list.html'
    context_object_name = 'responses'
    
    def dispatch(self, request, *args, **kwargs):
        self.survey = get_object_or_404(Survey, pk=self.kwargs['survey_id'])
        
        # Vérifier que l'utilisateur est l'auteur du sondage
        if self.survey.author != self.request.user:
            messages.error(request, "Vous n'avez pas la permission de voir les réponses à ce sondage.")
            return redirect('surveys:survey_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return SurveyResponse.objects.filter(survey=self.survey).order_by('-submitted_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['survey'] = self.survey
        return context
