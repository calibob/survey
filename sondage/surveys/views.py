import json
import uuid
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from statistics import mean, median, mode

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, FormView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib import messages
from django import forms
from django.db import transaction, models
import logging

logger = logging.getLogger(__name__)

from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Avg, F, Q, Func, Min, Max, StdDev, Sum, Value, ExpressionWrapper, FloatField
from django.db.models.functions import TruncDay

from .models import Survey, Question, QuestionOption, SurveyTheme, SurveyPageBreak
from responses.models import SurveyResponse, Answer
from .forms import (SurveyForm, QuestionForm, QuestionOptionFormSet, SurveyThemeForm, 
                    SurveyPageBreakForm, SurveyPreviewForm, ImportExportForm)

# Vue pour le tableau de bord administrateur
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'surveys/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Récupérer la période de filtrage depuis les paramètres GET
        period = self.request.GET.get('period', 'month')
        
        # Déterminer la date de début en fonction de la période
        today = timezone.now().date()
        if period == 'day':
            start_date = today
        elif period == 'week':
            start_date = today - timedelta(days=today.weekday())
        elif period == 'month':
            start_date = today.replace(day=1)
        elif period == 'year':
            start_date = today.replace(month=1, day=1)
        else:  # 'all' ou autre
            start_date = None
        
        # Filtrer les objets par période si nécessaire
        survey_filter = {'author': user}
        response_filter = {'survey__author': user}
        if start_date:
            survey_filter['created_at__gte'] = start_date
            response_filter['submitted_at__gte'] = start_date
        
        # Statistiques de base
        total_surveys = Survey.objects.filter(**survey_filter).count()
        total_responses = SurveyResponse.objects.filter(**response_filter).count()
        
        # Calcul du taux de complétion (pourcentage de sondages avec au moins une réponse)
        surveys_with_responses = Survey.objects.filter(
            author=user, 
            responses__isnull=False
        ).distinct().count()
        
        if total_surveys > 0:
            completion_rate = int((surveys_with_responses / total_surveys) * 100)
        else:
            completion_rate = 0
        
        # Temps moyen de complétion (si disponible)
        # Note: Nécessite un champ de temps dans le modèle de réponse
        avg_completion_time = "N/A"
        # Ici, on pourrait calculer le temps moyen si on stockait l'heure de début et de fin
        
        # Récupérer les sondages récents
        recent_surveys = Survey.objects.filter(author=user).order_by('-created_at')[:5]
        
        # Données pour le graphique de tendance des réponses
        last_30_days = timezone.now() - timedelta(days=30)
        
        # Utiliser TruncDay au lieu de Func(DATE) pour être compatible avec timezone
        response_by_day = SurveyResponse.objects.filter(
            survey__author=user,
            submitted_at__gte=last_30_days
        ).annotate(
            day=TruncDay('submitted_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Préparer les données pour le graphique
        dates = []
        counts = []
        
        # Créer un dictionnaire de dates formatées et comptes
        date_counts = {}
        for item in response_by_day:
            if item['day']:
                date_str = item['day'].strftime('%Y-%m-%d')
                date_counts[date_str] = item['count']
        
        # Remplir avec des zéros pour les jours sans réponses
        current_date = (timezone.now() - timedelta(days=30)).date()
        end_date = timezone.now().date()
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(date_str)
            counts.append(date_counts.get(date_str, 0))
            current_date += timedelta(days=1)
        
        # Distribution des types de questions
        question_types = Question.objects.filter(
            survey__author=user
        ).values('question_type').annotate(
            count=Count('id')
        )
        
        question_types_dict = {
            'single': 'Choix unique',
            'multiple': 'Choix multiple',
            'text': 'Texte libre',
            'scale': 'Échelle',
            'date': 'Date',
            'number': 'Nombre'
        }
        
        question_types_labels = []
        question_types_counts = []
        
        for qt in question_types:
            question_types_labels.append(question_types_dict.get(qt['question_type'], qt['question_type']))
            question_types_counts.append(qt['count'])
        
        # Activités récentes (réponses, créations de sondages, etc.)
        recent_activities = []
        
        # Réponses récentes
        recent_responses = SurveyResponse.objects.filter(
            survey__author=user
        ).order_by('-submitted_at')[:10]
        
        for response in recent_responses:
            recent_activities.append({
                'type': 'response',
                'text': f'Nouvelle réponse au sondage "{response.survey.title}"',
                'timestamp': response.submitted_at
            })
        
        # Sondages récemment créés
        for survey in recent_surveys:
            recent_activities.append({
                'type': 'survey_created',
                'text': f'Création du sondage "{survey.title}"',
                'timestamp': survey.created_at
            })
        
        # Trier les activités par date
        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_activities = recent_activities[:10]  # Limiter à 10 activités
        
        # Ajouter toutes les données au contexte
        context.update({
            'total_surveys': total_surveys,
            'total_responses': total_responses,
            'completion_rate': completion_rate,
            'avg_completion_time': avg_completion_time,
            'recent_surveys': recent_surveys,
            'recent_activities': recent_activities,
            'response_dates': json.dumps(dates),
            'response_counts': json.dumps(counts),
            'question_types_labels': json.dumps(question_types_labels),
            'question_types_counts': json.dumps(question_types_counts),
            'period': period
        })
        
        return context

# Vue pour la page d'accueil
class HomeView(ListView):
    model = Survey
    template_name = 'surveys/home.html'
    context_object_name = 'surveys'
    
    def get_queryset(self):
        return Survey.objects.filter(is_published=True).order_by('-created_at')

# Vues pour les sondages
class SurveyListView(ListView):
    model = Survey
    template_name = 'surveys/survey_list.html'
    context_object_name = 'surveys'
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Survey.objects.none()
            
        # Filtrer par statut d'archivage
        show_archived = self.request.GET.get('archived', 'false') == 'true'
        
        # Base de la requête pour les sondages de l'utilisateur
        queryset = Survey.objects.filter(author=self.request.user)
        
        # Filtrer selon le statut d'archivage
        queryset = queryset.filter(is_archived=show_archived)
        
        # Tri par date de création (les plus récents d'abord)
        return queryset.order_by('-created_at')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Déterminer si on affiche les sondages archivés ou actifs
        show_archived = self.request.GET.get('archived', 'false') == 'true'
        context['show_archived'] = show_archived
        
        # Compter le nombre total de sondages actifs et archivés
        if self.request.user.is_authenticated:
            context['active_count'] = Survey.objects.filter(
                author=self.request.user, 
                is_archived=False
            ).count()
            
            context['archived_count'] = Survey.objects.filter(
                author=self.request.user, 
                is_archived=True
            ).count()
        
        # Ajout des statistiques pour chaque sondage
        for survey in context['surveys']:
            survey.response_count = survey.responses.count()
            survey.question_count = survey.questions.count()
            survey.is_active = survey.is_active()
            
        return context

class SurveyCreateView(LoginRequiredMixin, CreateView):
    model = Survey
    form_class = SurveyForm
    template_name = 'surveys/survey_form.html'
    success_url = reverse_lazy('surveys:survey_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['themes'] = SurveyTheme.objects.filter(is_public=True) | SurveyTheme.objects.filter(author=self.request.user)
        context['is_creation'] = True
        return context
        
    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.access_token = str(uuid.uuid4())  # Génération d'un token d'accès unique
        messages.success(self.request, 'Le sondage a été créé avec succès.')
        return super().form_valid(form)

class SurveyUpdateView(LoginRequiredMixin, UpdateView):
    model = Survey
    form_class = SurveyForm
    template_name = 'surveys/survey_form.html'
    
    def get_queryset(self):
        return Survey.objects.filter(author=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['themes'] = SurveyTheme.objects.filter(is_public=True) | SurveyTheme.objects.filter(author=self.request.user)
        context['is_creation'] = False
        context['pagebreaks'] = SurveyPageBreak.objects.filter(survey=self.object).order_by('order')
        return context
    
    def get_success_url(self):
        return reverse('surveys:survey_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Si le token d'accès n'existe pas encore, en créer un
        if not form.instance.access_token:
            form.instance.access_token = str(uuid.uuid4())
        messages.success(self.request, 'Le sondage a été mis à jour avec succès.')
        return super().form_valid(form)

class SurveyDetailView(DetailView):
    model = Survey
    template_name = 'surveys/survey_detail.html'
    context_object_name = 'survey'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all().order_by('order')
        context['is_owner'] = self.object.author == self.request.user
        context['pagebreaks'] = SurveyPageBreak.objects.filter(survey=self.object).order_by('order')
        
        # URL de partage
        context['public_url'] = self.request.build_absolute_uri(
            reverse('surveys:survey_respond', kwargs={'pk': self.object.pk})
        )
        context['private_url'] = self.request.build_absolute_uri(
            reverse('surveys:survey_respond_private', kwargs={'token': self.object.access_token})
        )
        
        # Statistiques
        context['response_count'] = self.object.responses.count()
        context['is_active'] = self.object.is_active()
        
        return context

class SurveyDeleteView(LoginRequiredMixin, DeleteView):
    model = Survey
    template_name = 'surveys/survey_confirm_delete.html'
    success_url = reverse_lazy('surveys:survey_list')
    
    def get_queryset(self):
        return Survey.objects.filter(author=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Le sondage a été supprimé avec succès.')
        return super().delete(request, *args, **kwargs)

class ArchiveSurveyView(LoginRequiredMixin, View):
    """
    Vue permettant d'archiver ou de désarchiver un sondage.
    Cette fonctionnalité permet aux utilisateurs de garder leur liste de sondages organisée
    en archivant les sondages terminés ou inactifs.
    """
    
    def post(self, request, pk):
        survey = get_object_or_404(Survey, pk=pk, author=request.user)
        
        # Inverser l'état d'archivage
        if survey.is_archived:
            survey.is_archived = False
            survey.archived_at = None
            message = 'Le sondage a été désarchivé avec succès.'
        else:
            survey.is_archived = True
            survey.archived_at = timezone.now()
            message = 'Le sondage a été archivé avec succès.'
        
        survey.save(update_fields=['is_archived', 'archived_at'])
        messages.success(request, message)
        
        # Rediriger vers la page précédente ou la liste des sondages
        next_url = request.POST.get('next', reverse('surveys:survey_list'))
        return HttpResponseRedirect(next_url)

# Vues pour les questions
@login_required
def question_create_view(request, survey_id):
    """Vue ultra-simplifiée pour ajouter une question"""
    # Obtenir le sondage ou retourner 404 si non trouvé ou n'appartient pas à l'utilisateur
    survey = get_object_or_404(Survey, pk=survey_id, author=request.user)
    
    if request.method == 'POST':
        # Débogage
        logger.error("==== DÉBUT DU TRAITEMENT DE LA QUESTION ====")
        
        # Récupérer les données du formulaire
        question_text = request.POST.get('text', '').strip()
        question_type = request.POST.get('question_type', '')
        question_required = request.POST.get('required', '') == 'on'
        question_order = request.POST.get('order', '0')
        
        logger.error(f"Texte: {question_text}")
        logger.error(f"Type: {question_type}")
        logger.error(f"Obligatoire: {question_required}")
        logger.error(f"Ordre: {question_order}")
        
        # Valider le formulaire manuellement
        errors = []
        if not question_text:
            errors.append("Le texte de la question est obligatoire.")
        if not question_type:
            errors.append("Le type de question est obligatoire.")
        
        # Si le formulaire est valide, créer la question
        if not errors:
            try:
                # Convertir l'ordre en entier
                try:
                    order = int(question_order)
                except (ValueError, TypeError):
                    order = 0
                
                # Créer la question
                question = Question.objects.create(
                    text=question_text,
                    question_type=question_type,
                    required=question_required,
                    order=order,
                    survey=survey
                )
                
                logger.error(f"Question créée avec ID: {question.id}")
                
                # Traiter les options si nécessaire
                if question_type in ['single', 'multiple']:
                    # Récupérer toutes les options
                    option_texts = []
                    option_indices = []
                    
                    # Parcourir tous les paramètres POST pour trouver les options
                    for key, value in request.POST.items():
                        if key.startswith('option_text'):
                            option_texts.append(value)
                            # Extraire l'indice à partir du nom du champ (ex: option_text_0 -> 0)
                            try:
                                index = int(key.split('_')[-1])
                                option_indices.append(index)
                            except (ValueError, IndexError):
                                option_indices.append(len(option_indices))
                    
                    logger.error(f"Options trouvées: {option_texts}")
                    
                    # Créer les options
                    for i, text in enumerate(option_texts):
                        if text.strip():
                            try:
                                # Récupérer l'ordre
                                order_key = f'option_order_{option_indices[i]}'
                                order_value = request.POST.get(order_key, str(i))
                                try:
                                    order = int(order_value)
                                except (ValueError, TypeError):
                                    order = i
                                    
                                # Récupérer si c'est l'option par défaut
                                default_key = f'option_is_default_{option_indices[i]}'
                                is_default = request.POST.get(default_key) == 'on'
                                
                                # Créer l'option
                                option = QuestionOption.objects.create(
                                    question=question,
                                    text=text,
                                    order=order,
                                    is_default=is_default
                                )
                                logger.error(f"Option créée: {option.text}")
                            except Exception as e:
                                logger.error(f"Erreur lors de la création de l'option {i}: {str(e)}")
                
                messages.success(request, 'La question a été ajoutée avec succès.')
                return redirect('surveys:survey_detail', pk=survey.id)
            except Exception as e:
                logger.error(f"Exception lors de la création de la question: {str(e)}")
                errors.append(f"Erreur lors de la création de la question: {str(e)}")
        
        # Si des erreurs sont présentes, les afficher
        if errors:
            for error in errors:
                messages.error(request, error)
    
    # Préparer le formulaire vide pour la méthode GET
    form = QuestionForm(survey=survey)
    
    # Rendre le template
    return render(request, 'surveys/question_form_simple.html', {
        'form': form,
        'survey': survey,
        'available_questions': survey.questions.all().order_by('order'),
    })

@login_required
def question_update_view(request, pk):
    """Vue simplifiée pour modifier une question"""
    # Obtenir la question ou retourner 404
    question = get_object_or_404(Question, pk=pk)
    survey = question.survey
    
    # Vérifier les permissions
    if survey.author != request.user:
        messages.error(request, "Vous n'avez pas la permission de modifier cette question.")
        return redirect('surveys:survey_list')
    
    # Déterminer si la question a déjà des options
    has_options = question.options.exists()
    
    if request.method == 'POST':
        # Debug
        logger.error(f"Début mise à jour question {pk} - POST data: {request.POST}")
        
        # Extraction des données du formulaire
        form_data = {
            'text': request.POST.get('text', '').strip(),
            'question_type': request.POST.get('question_type', ''),
            'required': request.POST.get('required', '') == 'on',
            'order': request.POST.get('order', str(question.order))
        }
        
        # Validation manuelle
        errors = []
        if not form_data['text']:
            errors.append("Le texte de la question est obligatoire.")
        if not form_data['question_type']:
            errors.append("Le type de question est obligatoire.")
        
        # Si pas d'erreur, procéder à la mise à jour
        if not errors:
            try:
                # Utiliser une transaction pour garantir la cohérence
                with transaction.atomic():
                    # 1. Mettre à jour les attributs principaux de la question
                    question.text = form_data['text']
                    question.question_type = form_data['question_type']
                    question.required = form_data['required']
                    
                    # Convertir l'ordre en entier
                    try:
                        question.order = int(form_data['order'])
                    except (ValueError, TypeError):
                        # Garder l'ordre actuel en cas d'erreur
                        pass
                    
                    # Enregistrer les modifications de base
                    question.save()
                    logger.error(f"Question {pk} mise à jour: {question.text}, Type: {question.question_type}")
                    
                    # 2. Gérer les options pour les types qui en nécessitent
                    if question.question_type in ['single', 'multiple']:
                        # Récupérer les options depuis le formulaire
                        options_to_save = []
                        option_ids_to_keep = []
                        
                        # Parcourir les données POST pour trouver les options
                        for key in request.POST:
                            if key.startswith('option_text_'):
                                try:
                                    idx = int(key.split('_')[-1])
                                    text = request.POST.get(key, '').strip()
                                    
                                    # Ne pas traiter les options vides
                                    if not text:
                                        continue
                                    
                                    # Récupérer les informations associées
                                    option_id = request.POST.get(f'option_id_{idx}', '')
                                    
                                    # Déterminer l'ordre
                                    try:
                                        order = int(request.POST.get(f'option_order_{idx}', str(idx)))
                                    except (ValueError, TypeError):
                                        order = idx
                                    
                                    # Déterminer si c'est l'option par défaut
                                    is_default = request.POST.get(f'option_is_default_{idx}') == 'on'
                                    
                                    # Ajouter à la liste des options à traiter
                                    options_to_save.append({
                                        'id': option_id.strip() if option_id and option_id.strip() and option_id.strip().lower() != 'none' else None,
                                        'text': text,
                                        'order': order,
                                        'is_default': is_default
                                    })
                                    
                                    # Garder trace des IDs existants à conserver
                                    if option_id and option_id.strip() and option_id.strip().lower() != 'none' and option_id.strip().isdigit():
                                        option_ids_to_keep.append(option_id.strip())
                                        
                                except (ValueError, IndexError) as e:
                                    logger.error(f"Erreur lors du traitement de l'option {key}: {e}")
                        
                        logger.error(f"Options extraites: {options_to_save}")
                        logger.error(f"IDs à conserver: {option_ids_to_keep}")
                        
                        # Supprimer les options qui ne sont plus présentes dans le formulaire
                        if option_ids_to_keep:
                            # Identifier les options à garder et à supprimer
                            existing_options = list(question.options.all())
                            options_to_delete = []
                            
                            for option in existing_options:
                                if str(option.id) not in option_ids_to_keep:
                                    options_to_delete.append(option.id)
                            
                            if options_to_delete:
                                question.options.filter(id__in=options_to_delete).delete()
                                logger.error(f"Suppression de {len(options_to_delete)} options non utilisées")
                        else:
                            # Si nous avons des options à sauvegarder mais aucun ID à conserver, supprimer toutes les options existantes
                            if options_to_save and question.options.exists():
                                question.options.all().delete()
                                logger.error("Toutes les options existantes ont été supprimées pour les remplacer par de nouvelles")

                        
                        # Créer ou mettre à jour chaque option
                        for opt in options_to_save:
                            if opt['id']:
                                # Mettre à jour l'option existante
                                try:
                                    option = QuestionOption.objects.get(id=opt['id'], question=question)
                                    option.text = opt['text']
                                    option.order = opt['order']
                                    option.is_default = opt['is_default']
                                    option.save()
                                    logger.error(f"Option mise à jour: ID={option.id}, Texte={option.text}")
                                except QuestionOption.DoesNotExist:
                                    # Créer une nouvelle option si l'ID n'existe pas
                                    option = QuestionOption.objects.create(
                                        question=question,
                                        text=opt['text'],
                                        order=opt['order'],
                                        is_default=opt['is_default']
                                    )
                                    logger.error(f"Option créée avec ID inexistant: ID={option.id}, Texte={option.text}")
                            else:
                                # Créer une nouvelle option
                                option = QuestionOption.objects.create(
                                    question=question,
                                    text=opt['text'],
                                    order=opt['order'],
                                    is_default=opt['is_default']
                                )
                                logger.error(f"Nouvelle option créée: ID={option.id}, Texte={option.text}")
                        
                        # S'assurer qu'il y a au moins une option
                        if not options_to_save and not question.options.exists():
                            # Créer une option par défaut
                            QuestionOption.objects.create(
                                question=question,
                                text="Option 1",
                                order=0,
                                is_default=True
                            )
                            logger.error("Option par défaut créée")
                    
                    # Si le type ne nécessite pas d'options, les supprimer
                    elif question.question_type not in ['single', 'multiple']:
                        count = question.options.count()
                        if count > 0:
                            question.options.all().delete()
                            logger.error(f"{count} options supprimées car le type ne nécessite pas d'options")
                    
                    # Confirmer la mise à jour
                    messages.success(request, 'La question a été mise à jour avec succès.')
                    logger.error(f"Question {pk} mise à jour avec succès, redirection")
                    return redirect('surveys:survey_detail', pk=survey.id)
            
            except Exception as e:
                import traceback
                logger.error(f"ERREUR lors de la mise à jour de la question {pk}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                errors.append(f"Une erreur est survenue: {str(e)}")
        
        # Afficher les erreurs
        for error in errors:
            messages.error(request, error)
    
    # Préparer le contexte pour le template
    form = QuestionForm(instance=question, survey=survey)
    formset = QuestionOptionFormSet(instance=question)
    
    # Vérifier à nouveau si la question a des options
    has_options = question.options.exists()
    
    # Rendre le template
    return render(request, 'surveys/question_form.html', {
        'form': form,
        'survey': survey,
        'question': question,
        'options_formset': formset,
        'available_questions': survey.questions.all().exclude(id=question.id).order_by('order'),
        'has_options': has_options,
    })

# Vue pour la participation à un sondage
class SurveyResponseView(DetailView):
    model = Survey
    template_name = 'surveys/survey_respond.html'
    context_object_name = 'survey'
    
    def dispatch(self, request, *args, **kwargs):
        survey = self.get_object()
        
        # Vérifier si le sondage est publié
        if not survey.is_published and survey.author != request.user:
            messages.error(request, "Ce sondage n'est pas disponible.")
            return redirect('surveys:home')
        
        # Vérifier les dates de début et de fin
        if not survey.is_active() and survey.author != request.user:
            messages.error(request, "Ce sondage n'est plus disponible.")
            return redirect('surveys:home')
            
        # Vérifier si un mot de passe est requis
        if survey.password and not request.session.get(f'survey_access_{survey.id}'):
            return redirect('surveys:survey_password', pk=survey.id)
            
        # Vérifier si la participation multiple est autorisée
        if not survey.allow_multiple_submissions:
            if request.session.get(f'survey_completed_{survey.id}'):
                messages.info(request, "Vous avez déjà participé à ce sondage.")
                return redirect('surveys:survey_thankyou', pk=survey.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all().order_by('order')
        context['pagebreaks'] = SurveyPageBreak.objects.filter(survey=self.object).order_by('order')
        return context


# Vue pour l'accès à un sondage par token privé
class SurveyResponsePrivateView(DetailView):
    model = Survey
    template_name = 'surveys/survey_respond.html'
    context_object_name = 'survey'
    
    def get_object(self):
        token = self.kwargs.get('token')
        return get_object_or_404(Survey, access_token=token)
    
    def dispatch(self, request, *args, **kwargs):
        survey = self.get_object()
        
        # Vérifier les dates de début et de fin
        if not survey.is_active() and survey.author != request.user:
            messages.error(request, "Ce sondage n'est plus disponible.")
            return redirect('surveys:home')
            
        # Vérifier si un mot de passe est requis
        if survey.password and not request.session.get(f'survey_access_{survey.id}'):
            # Rediriger vers la page de mot de passe avec le token
            return redirect('surveys:survey_password_token', token=survey.access_token)
            
        # Vérifier si la participation multiple est autorisée
        if not survey.allow_multiple_submissions:
            if request.session.get(f'survey_completed_{survey.id}'):
                messages.info(request, "Vous avez déjà participé à ce sondage.")
                return redirect('surveys:survey_thankyou', pk=survey.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all().order_by('order')
        context['pagebreaks'] = SurveyPageBreak.objects.filter(survey=self.object).order_by('order')
        context['is_private'] = True  # Pour indiquer que c'est un accès privé
        return context


# Vue pour la vérification de mot de passe d'un sondage
class SurveyPasswordView(FormView):
    template_name = 'surveys/survey_password.html'
    form_class = forms.Form
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.survey = None
        self.token = kwargs.get('token', None)
        
        if self.token:
            self.survey = get_object_or_404(Survey, access_token=self.token)
        else:
            self.survey = get_object_or_404(Survey, pk=kwargs.get('pk'))
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['password'] = forms.CharField(
            widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'}),
            label='Mot de passe'
        )
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['survey'] = self.survey
        return context
    
    def form_valid(self, form):
        entered_password = form.cleaned_data['password']
        
        if entered_password == self.survey.password:
            # Mémoriser l'accès dans la session
            self.request.session[f'survey_access_{self.survey.id}'] = True
            
            # Rediriger vers le sondage
            if self.token:
                return redirect('surveys:survey_respond_private', token=self.token)
            return redirect('surveys:survey_respond', pk=self.survey.pk)
        else:
            form.add_error('password', "Le mot de passe est incorrect.")
            return self.form_invalid(form)


# Vue pour la page de remerciement après un sondage
class SurveyThankYouView(DetailView):
    model = Survey
    template_name = 'surveys/survey_thankyou.html'
    context_object_name = 'survey'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


# Vue pour la prévisualisation d'un sondage
class SurveyPreviewView(LoginRequiredMixin, FormView):
    template_name = 'surveys/survey_preview.html'
    form_class = SurveyPreviewForm
    
    def dispatch(self, request, *args, **kwargs):
        self.survey = get_object_or_404(Survey, pk=self.kwargs['pk'], author=request.user)
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['survey'] = self.survey
        context['questions'] = self.survey.questions.all().order_by('order')
        context['pagebreaks'] = self.survey.pagebreaks.all().order_by('order')
        context['preview'] = True
        
        # Déterminer le type d'appareil pour la prévisualisation
        preview_type = self.request.GET.get('device', 'desktop')
        if preview_type not in ['desktop', 'tablet', 'mobile']:
            preview_type = 'desktop'
        context['preview_type'] = preview_type
        
        return context


# Vue pour la gestion des thèmes de sondage
class SurveyThemeListView(LoginRequiredMixin, ListView):
    model = SurveyTheme
    template_name = 'surveys/theme_list.html'
    context_object_name = 'themes'
    
    def get_queryset(self):
        # Afficher les thèmes publics et ceux créés par l'utilisateur
        return SurveyTheme.objects.filter(
            models.Q(is_public=True) | models.Q(author=self.request.user)
        ).order_by('-created_at')


class SurveyThemeCreateView(LoginRequiredMixin, CreateView):
    model = SurveyTheme
    form_class = SurveyThemeForm
    template_name = 'surveys/theme_form.html'
    success_url = reverse_lazy('surveys:theme_list')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Le thème a été créé avec succès.')
        return super().form_valid(form)


class SurveyThemeUpdateView(LoginRequiredMixin, UpdateView):
    model = SurveyTheme
    form_class = SurveyThemeForm
    template_name = 'surveys/theme_form.html'
    
    def get_queryset(self):
        # Limiter aux thèmes créés par l'utilisateur
        return SurveyTheme.objects.filter(author=self.request.user)
    
    def get_success_url(self):
        return reverse('surveys:theme_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Le thème a été mis à jour avec succès.')
        return super().form_valid(form)


class SurveyThemeDeleteView(LoginRequiredMixin, DeleteView):
    model = SurveyTheme
    template_name = 'surveys/theme_confirm_delete.html'
    success_url = reverse_lazy('surveys:theme_list')
    
    def get_queryset(self):
        # Limiter aux thèmes créés par l'utilisateur
        return SurveyTheme.objects.filter(author=self.request.user)


# Vue pour la gestion des sauts de page
class PageBreakCreateView(LoginRequiredMixin, CreateView):
    model = SurveyPageBreak
    form_class = SurveyPageBreakForm
    template_name = 'surveys/pagebreak_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.survey = get_object_or_404(Survey, pk=self.kwargs['survey_id'], author=request.user)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['survey'] = self.survey
        return context
    
    def form_valid(self, form):
        form.instance.survey = self.survey
        messages.success(self.request, 'Le saut de page a été créé avec succès.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('surveys:survey_detail', kwargs={'pk': self.survey.pk})


class PageBreakUpdateView(LoginRequiredMixin, UpdateView):
    model = SurveyPageBreak
    form_class = SurveyPageBreakForm
    template_name = 'surveys/pagebreak_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.page_break = get_object_or_404(SurveyPageBreak, pk=self.kwargs['pk'])
        self.survey = self.page_break.survey
        
        if self.survey.author != request.user:
            messages.error(request, "Vous n'avez pas la permission de modifier ce saut de page.")
            return redirect('surveys:survey_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['survey'] = self.survey
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Le saut de page a été mis à jour avec succès.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('surveys:survey_detail', kwargs={'pk': self.survey.pk})


class PageBreakDeleteView(LoginRequiredMixin, DeleteView):
    model = SurveyPageBreak
    template_name = 'surveys/pagebreak_confirm_delete.html'
    
    def get_queryset(self):
        # Limiter aux sauts de page des sondages de l'utilisateur
        return SurveyPageBreak.objects.filter(survey__author=self.request.user)

# Vue pour l'exportation des résultats
class SurveyExportView(LoginRequiredMixin, FormView):
    template_name = 'surveys/survey_export.html'
    form_class = ImportExportForm
    
# Vue pour l'affichage des résultats d'un sondage
class SurveyResultsView(LoginRequiredMixin, DetailView):
    model = Survey
    template_name = 'surveys/survey_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey = self.get_object()
        
        # Vérifier que l'utilisateur est bien l'auteur du sondage
        if survey.author != self.request.user:
            raise PermissionDenied("Vous n'êtes pas autorisé à voir les résultats de ce sondage.")
        
        # Récupérer toutes les réponses
        responses = survey.responses.all()
        total_responses = responses.count()
        
        # Filtres (date)
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                responses = responses.filter(submitted_at__gte=start_date)
            except ValueError:
                pass
                
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
                responses = responses.filter(submitted_at__lte=end_date)
            except ValueError:
                pass
        
        # Préparer les données pour chaque question
        questions_data = []
        
        for question in survey.questions.all().order_by('position'):
            question_data = {
                'id': question.id,
                'text': question.text,
                'type': question.question_type,
                'answers': [],
                'stats': {}
            }
            
            # Récupérer les réponses pour cette question
            answers = Answer.objects.filter(response__in=responses, question=question)
            
            if question.question_type in ['single', 'multiple']:
                # Pour les questions à choix
                options = question.options.all()
                option_counts = defaultdict(int)
                
                for answer in answers:
                    # Pour les choix multiples, les valeurs sont stockées comme une liste JSON
                    if question.question_type == 'multiple' and answer.value:
                        try:
                            selected_options = json.loads(answer.value)
                            for option_id in selected_options:
                                option_counts[int(option_id)] += 1
                        except (json.JSONDecodeError, ValueError):
                            pass
                    # Pour les choix uniques
                    elif question.question_type == 'single' and answer.value:
                        try:
                            option_counts[int(answer.value)] += 1
                        except ValueError:
                            pass
                
                # Préparer les données pour le graphique
                labels = []
                data = []
                colors = []
                
                for option in options:
                    labels.append(option.text)
                    count = option_counts.get(option.id, 0)
                    data.append(count)
                    # Générer une couleur aléatoire ou utiliser une palette prédéfinie
                    colors.append(f'rgba({(option.id * 50) % 255}, {(option.id * 30) % 255}, {(option.id * 70) % 255}, 0.7)')
                
                question_data['chart_data'] = {
                    'labels': labels,
                    'datasets': [{
                        'data': data,
                        'backgroundColor': colors
                    }]
                }
                
                # Statistiques de base
                total_selections = sum(data)
                if total_selections > 0:
                    question_data['stats']['most_selected'] = labels[data.index(max(data))]
                    question_data['stats']['least_selected'] = labels[data.index(min(data))]
                    question_data['stats']['total_selections'] = total_selections
                
            elif question.question_type == 'text':
                # Pour les questions textuelles
                text_answers = [a.value for a in answers if a.value]
                question_data['answers'] = text_answers
                
                # Statistiques de base pour les textes
                question_data['stats']['total_answers'] = len(text_answers)
                question_data['stats']['average_length'] = int(sum(len(t) for t in text_answers) / max(1, len(text_answers)))
                
                # Analyse de mots-clés (fréquence de mots simples)
                word_counts = Counter()
                for text in text_answers:
                    # Diviser en mots et compter la fréquence
                    words = re.findall(r'\b\w+\b', text.lower())
                    word_counts.update(words)
                
                # Exclure les mots très courts et les mots communs (stop words)
                stop_words = {'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'a', 'au', 'aux', 'ce', 'ces', 'cette', 'en', 'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'qui', 'que', 'quoi', 'dont', 'où', 'pour', 'par', 'avec', 'sans', 'de', 'du', 'dans'}
                word_counts = {word: count for word, count in word_counts.items() if len(word) > 2 and word not in stop_words}
                
                # Top mots-clés
                top_words = word_counts.most_common(10)
                question_data['word_cloud'] = [{'text': word, 'size': count} for word, count in top_words]
                
            elif question.question_type == 'scale':
                # Pour les questions d'échelle
                scale_values = [int(a.value) for a in answers if a.value and a.value.isdigit()]
                
                if scale_values:
                    # Statistiques
                    question_data['stats']['average'] = round(sum(scale_values) / len(scale_values), 2)
                    question_data['stats']['median'] = median(scale_values) if scale_values else 'N/A'
                    question_data['stats']['min'] = min(scale_values)
                    question_data['stats']['max'] = max(scale_values)
                    
                    # Préparer les données pour l'histogramme
                    ratings = Counter(scale_values)
                    labels = sorted(ratings.keys())
                    data = [ratings[label] for label in labels]
                    
                    question_data['chart_data'] = {
                        'labels': labels,
                        'datasets': [{
                            'data': data,
                            'backgroundColor': 'rgba(75, 192, 192, 0.7)'
                        }]
                    }
            
            elif question.question_type in ['date', 'number']:
                # Pour les questions de date ou numériques
                numeric_values = []
                
                for answer in answers:
                    if question.question_type == 'date' and answer.value:
                        try:
                            # Convertir la date en timestamp pour l'analyse numérique
                            date_obj = datetime.strptime(answer.value, '%Y-%m-%d')
                            question_data['answers'].append(answer.value)  # Stocker la date originale
                        except ValueError:
                            pass
                    elif question.question_type == 'number' and answer.value:
                        try:
                            value = float(answer.value)
                            numeric_values.append(value)
                            question_data['answers'].append(value)
                        except ValueError:
                            pass
                
                # Statistiques pour les valeurs numériques
                if numeric_values:
                    question_data['stats']['average'] = round(sum(numeric_values) / len(numeric_values), 2)
                    question_data['stats']['median'] = median(numeric_values)
                    question_data['stats']['min'] = min(numeric_values)
                    question_data['stats']['max'] = max(numeric_values)
                    
                    # Pour les questions numériques, créer un histogramme simple
                    if question.question_type == 'number':
                        # Division en 5-10 bins pour l'histogramme
                        min_val = min(numeric_values)
                        max_val = max(numeric_values)
                        bin_size = max(1, (max_val - min_val) / 8)  # Au moins 1, max 8 bins
                        
                        bins = []
                        current = min_val
                        while current <= max_val:
                            bins.append(current)
                            current += bin_size
                        
                        # Compter le nombre de valeurs dans chaque bin
                        bin_counts = [0] * (len(bins) - 1)
                        for value in numeric_values:
                            for i in range(len(bins) - 1):
                                if bins[i] <= value < bins[i + 1] or (i == len(bins) - 2 and value == bins[i + 1]):
                                    bin_counts[i] += 1
                                    break
                        
                        # Formater les labels pour l'affichage
                        bin_labels = [f"{round(bins[i], 1)}-{round(bins[i+1], 1)}" for i in range(len(bins) - 1)]
                        
                        question_data['chart_data'] = {
                            'labels': bin_labels,
                            'datasets': [{
                                'data': bin_counts,
                                'backgroundColor': 'rgba(153, 102, 255, 0.7)'
                            }]
                        }
            
            questions_data.append(question_data)
        
        # Informations générales sur les réponses
        context['total_responses'] = total_responses
        context['questions_data'] = questions_data
        context['json_questions_data'] = json.dumps(questions_data)
        
        # Ajouter les dates de filtrage au contexte
        context['start_date'] = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else ''
        context['end_date'] = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else ''
        
        return context
    
    def dispatch(self, request, *args, **kwargs):
        self.survey = get_object_or_404(Survey, pk=self.kwargs['pk'], author=request.user)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['survey'] = self.survey
        return context
    
    def form_valid(self, form):
        format_type = form.cleaned_data['format_type']
        include_responses = form.cleaned_data.get('include_responses', True)
        
        # Préparer les données pour l'exportation
        data = {
            'survey': {
                'id': self.survey.id,
                'title': self.survey.title,
                'description': self.survey.description,
                'created_at': self.survey.created_at.isoformat(),
            },
            'questions': []
        }
        
        # Ajouter les questions
        for question in self.survey.questions.all().order_by('order'):
            q_data = {
                'id': question.id,
                'text': question.text,
                'type': question.question_type,
                'required': question.required,
                'order': question.order,
                'options': []
            }
            
            # Ajouter les options si applicable
            if question.question_type in ['single', 'multiple']:
                for option in question.options.all().order_by('order'):
                    q_data['options'].append({
                        'id': option.id,
                        'text': option.text,
                        'order': option.order
                    })
            
            data['questions'].append(q_data)
        
        # Ajouter les réponses si demandé
        if include_responses:
            data['responses'] = []
            for response in self.survey.responses.all():
                r_data = {
                    'id': response.id,
                    'submitted_at': response.submitted_at.isoformat(),
                    'ip_address': response.ip_address,
                    'answers': []
                }
                
                for answer in response.answers.all():
                    a_data = {
                        'question_id': answer.question.id,
                        'question_text': answer.question.text,
                        'response_text': answer.response_text,
                    }
                    r_data['answers'].append(a_data)
                
                data['responses'].append(r_data)
        
        # Générer le fichier selon le format demandé
        if format_type == 'json':
            response = HttpResponse(json.dumps(data, indent=4), content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{self.survey.slug}_{timezone.now().strftime("%Y%m%d")}.json"'
            return response
        elif format_type == 'csv':
            # Implémentation basique pour l'exemple - à améliorer pour un cas réel
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{self.survey.slug}_{timezone.now().strftime("%Y%m%d")}.csv"'
            
            # Implémentation simplifiée - à compléter
            import csv
            writer = csv.writer(response)
            writer.writerow(['Question', 'Type', 'Réponse', 'Date'])
            
            # Ajouter les réponses si demandé
            if include_responses:
                for response_obj in self.survey.responses.all():
                    for answer in response_obj.answers.all():
                        writer.writerow([
                            answer.question.text,
                            answer.question.question_type,
                            answer.response_text,
                            response_obj.submitted_at.strftime("%Y-%m-%d %H:%M")
                        ])
            
            return response
        elif format_type == 'excel':
            # À implémenter avec une bibliothèque comme openpyxl ou pandas
            messages.warning(self.request, "L'exportation Excel sera disponible prochainement.")
            return redirect('surveys:survey_detail', pk=self.survey.pk)
        
        messages.error(self.request, "Format d'exportation non pris en charge.")
        return self.form_invalid(form)
