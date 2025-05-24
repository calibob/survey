from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from colorfield.fields import ColorField
import uuid
import secrets

class Survey(models.Model):
    # Informations de base
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surveys')
    is_published = models.BooleanField(default=False, verbose_name="Publié")
    
    # Personnalisation (Étape 2)
    primary_color = ColorField(default='#007bff', verbose_name="Couleur principale")
    background_color = ColorField(default='#ffffff', verbose_name="Couleur d'arrière-plan")
    logo = models.ImageField(upload_to='survey_logos/', blank=True, null=True, verbose_name="Logo")
    completion_message = models.TextField(blank=True, default="Merci d'avoir répondu à ce sondage !", verbose_name="Message de fin")
    
    # Restrictions (Étape 2)
    access_token = models.CharField(max_length=64, blank=True, null=True, verbose_name="Token d'accès")
    password = models.CharField(max_length=128, blank=True, null=True, verbose_name="Mot de passe")
    start_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de début")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de fin")
    allow_multiple_submissions = models.BooleanField(default=True, verbose_name="Autorise plusieurs participations")
    track_ip = models.BooleanField(default=True, verbose_name="Enregistrer les adresses IP")
    
    # Archivage (Étape 3)
    is_archived = models.BooleanField(default=False, verbose_name="Archivé")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Date d'archivage")
    
    class Meta:
        verbose_name = "Sondage"
        verbose_name_plural = "Sondages"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Générer un slug unique à partir du titre
        if not self.slug:
            self.slug = slugify(self.title)
            # Ajouter un identifiant unique si le slug existe déjà
            if Survey.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-{str(uuid.uuid4())[:8]}"
        
        # Générer un token d'accès unique pour les liens privés
        if not self.access_token:
            self.access_token = secrets.token_urlsafe(32)
            
        super().save(*args, **kwargs)
        
    def is_active(self):
        """Vérifie si le sondage est actif selon les dates définies"""
        now = timezone.now()
        
        if not self.is_published:
            return False
            
        if self.start_date and now < self.start_date:
            return False
            
        if self.end_date and now > self.end_date:
            return False
            
        return True
        
    def get_private_url(self):
        """Retourne l'URL privée avec le token d'accès"""
        return f"/surveys/{self.id}/respond/{self.access_token}/"

class Question(models.Model):
    QUESTION_TYPES = [
        ('single', 'Choix unique'),
        ('multiple', 'Choix multiple'),
        ('text', 'Texte libre'),
        ('scale', 'Échelle'),
        ('date', 'Date'),
        ('email', 'Email'),
        ('number', 'Nombre'),
    ]
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500, verbose_name="Texte de la question")
    description = models.TextField(blank=True, verbose_name="Description ou aide")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='single', verbose_name="Type de question")
    required = models.BooleanField(default=True, verbose_name="Obligatoire")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    
    # Champs pour l'échelle
    scale_min = models.IntegerField(default=1, verbose_name="Valeur minimale de l'échelle")
    scale_max = models.IntegerField(default=5, verbose_name="Valeur maximale de l'échelle")
    scale_min_label = models.CharField(max_length=50, blank=True, verbose_name="Étiquette pour la valeur minimale")
    scale_max_label = models.CharField(max_length=50, blank=True, verbose_name="Étiquette pour la valeur maximale")
    
    # Logique conditionnelle (Étape 2)
    depends_on = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dependent_questions', verbose_name="Dépend de la question")
    condition_value = models.CharField(max_length=255, blank=True, verbose_name="Valeur de la condition")
    condition_operator = models.CharField(max_length=15, choices=[
        ('eq', 'Est égal à'),
        ('neq', 'Est différent de'),
        ('gt', 'Est supérieur à'),
        ('lt', 'Est inférieur à'),
        ('contains', 'Contient'),
        ('not_contains', 'Ne contient pas'),
    ], default='eq', blank=True, verbose_name="Opérateur de condition")
    
    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['survey', 'order']
    
    def __str__(self):
        return f"{self.text} ({self.get_question_type_display()})"

class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=200, verbose_name="Texte de l'option")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    image = models.ImageField(upload_to='option_images/', blank=True, null=True, verbose_name="Image")
    is_default = models.BooleanField(default=False, verbose_name="Option par défaut")
    
    # Pour les questions à échelle, on peut stocker des valeurs numériques
    numeric_value = models.IntegerField(null=True, blank=True, verbose_name="Valeur numérique")
    
    class Meta:
        verbose_name = "Option de question"
        verbose_name_plural = "Options de question"
        ordering = ['question', 'order']
    
    def __str__(self):
        return self.text


class SurveyPageBreak(models.Model):
    """Modèle pour permettre de diviser un sondage en plusieurs pages"""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='page_breaks')
    title = models.CharField(max_length=200, blank=True, verbose_name="Titre de la page")
    description = models.TextField(blank=True, verbose_name="Description de la page")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    
    class Meta:
        verbose_name = "Saut de page"
        verbose_name_plural = "Sauts de page"
        ordering = ['survey', 'order']
    
    def __str__(self):
        return f"Page {self.order + 1} - {self.title}" if self.title else f"Page {self.order + 1}"


class SurveyTheme(models.Model):
    """Modèle pour les thèmes réutilisables de sondage"""
    name = models.CharField(max_length=100, verbose_name="Nom du thème")
    description = models.TextField(blank=True, verbose_name="Description")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='themes')
    primary_color = ColorField(default='#007bff', verbose_name="Couleur principale")
    background_color = ColorField(default='#ffffff', verbose_name="Couleur d'arrière-plan")
    button_color = ColorField(default='#007bff', verbose_name="Couleur des boutons")
    text_color = ColorField(default='#212529', verbose_name="Couleur du texte")
    logo = models.ImageField(upload_to='theme_logos/', blank=True, null=True, verbose_name="Logo")
    css = models.TextField(blank=True, verbose_name="CSS personnalisé")
    is_public = models.BooleanField(default=False, verbose_name="Thème public")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Thème de sondage"
        verbose_name_plural = "Thèmes de sondage"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
