from django import forms
from django.utils import timezone
from .models import Survey, Question, QuestionOption, SurveyTheme, SurveyPageBreak
from colorfield.fields import ColorField

class SurveyForm(forms.ModelForm):
    # Champs supplémentaires pour la sélection de dates
    start_date_field = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label="Date de début"
    )
    end_date_field = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label="Date de fin"
    )
    
    class Meta:
        model = Survey
        fields = [
            # Informations de base
            'title', 'description', 'is_published',
            # Personnalisation
            'primary_color', 'background_color', 'logo', 'completion_message',
            # Restrictions
            'password', 'allow_multiple_submissions', 'track_ip'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'completion_message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}, render_value=True),
            'primary_color': forms.TextInput(attrs={'class': 'form-control colorfield_field'}),
            'background_color': forms.TextInput(attrs={'class': 'form-control colorfield_field'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        # Initialiser les champs de date avec les valeurs de l'instance si elle existe
        if instance:
            if instance.start_date:
                self.fields['start_date_field'].initial = instance.start_date
            if instance.end_date:
                self.fields['end_date_field'].initial = instance.end_date
                
        # Rendre certains champs optionnels
        self.fields['primary_color'].required = False
        self.fields['background_color'].required = False
        self.fields['password'].required = False
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Sauvegarder les dates
        instance.start_date = self.cleaned_data.get('start_date_field')
        instance.end_date = self.cleaned_data.get('end_date_field')
        
        if commit:
            instance.save()
        return instance

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'text', 'description', 'question_type', 'required', 'order',
            'scale_min', 'scale_max', 'scale_min_label', 'scale_max_label',
            'depends_on', 'condition_operator', 'condition_value'
        ]
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'question_type': forms.Select(attrs={'class': 'form-control', 'id': 'question-type-select'}),
            'required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'scale_min': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'scale_max': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'scale_min_label': forms.TextInput(attrs={'class': 'form-control'}),
            'scale_max_label': forms.TextInput(attrs={'class': 'form-control'}),
            'depends_on': forms.Select(attrs={'class': 'form-control'}),
            'condition_operator': forms.Select(attrs={'class': 'form-control'}),
            'condition_value': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        survey = kwargs.pop('survey', None)
        super().__init__(*args, **kwargs)
        
        # Restreindre les questions dépendantes à celles du même sondage
        if survey:
            self.fields['depends_on'].queryset = Question.objects.filter(survey=survey).exclude(
                id=self.instance.id if self.instance and self.instance.id else None
            )
        else:
            self.fields['depends_on'].queryset = Question.objects.none()
            
        # Pour les nouvelles questions, définir des valeurs par défaut pour l'échelle
        if not self.instance.pk:
            self.fields['scale_min'].initial = 1
            self.fields['scale_max'].initial = 5
            
        # Ajouter des classes pour le contrôle de visibilité par JavaScript
        self.fields['scale_min'].widget.attrs['class'] += ' scale-field'
        self.fields['scale_max'].widget.attrs['class'] += ' scale-field'
        self.fields['scale_min_label'].widget.attrs['class'] += ' scale-field'
        self.fields['scale_max_label'].widget.attrs['class'] += ' scale-field'
        self.fields['depends_on'].widget.attrs['class'] += ' condition-field'
        self.fields['condition_operator'].widget.attrs['class'] += ' condition-field'
        self.fields['condition_value'].widget.attrs['class'] += ' condition-field'

class QuestionOptionForm(forms.ModelForm):
    class Meta:
        model = QuestionOption
        fields = ['text', 'order', 'is_default', 'image', 'numeric_value']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'numeric_value': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# Configuration améliorée du formset pour les options de question
QuestionOptionFormSet = forms.inlineformset_factory(
    Question, 
    QuestionOption,
    form=QuestionOptionForm,
    extra=4,  # Augmentation du nombre d'options supplémentaires
    can_delete=True,
    validate_max=True,
    validate_min=True,
    max_num=10,  # Nombre maximum d'options
    min_num=1,   # Au moins une option requise pour les questions à choix
)


class SurveyThemeForm(forms.ModelForm):
    class Meta:
        model = SurveyTheme
        fields = ['name', 'description', 'primary_color', 'background_color', 
                 'button_color', 'text_color', 'logo', 'css', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control colorfield_field'}),
            'background_color': forms.TextInput(attrs={'class': 'form-control colorfield_field'}),
            'button_color': forms.TextInput(attrs={'class': 'form-control colorfield_field'}),
            'text_color': forms.TextInput(attrs={'class': 'form-control colorfield_field'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'css': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SurveyPageBreakForm(forms.ModelForm):
    class Meta:
        model = SurveyPageBreak
        fields = ['title', 'description', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class SurveyPreviewForm(forms.Form):
    """Formulaire pour la prévisualisation d'un sondage"""
    preview_type = forms.ChoiceField(
        choices=[('desktop', 'Ordinateur'), ('tablet', 'Tablette'), ('mobile', 'Mobile')],
        initial='desktop',
        widget=forms.RadioSelect(attrs={'class': 'preview-type-radio'})
    )


class ImportExportForm(forms.Form):
    """Formulaire pour l'importation et l'exportation de sondages"""
    file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.json,.csv,.xlsx'}),
        help_text="Formats acceptés: JSON, CSV, Excel"
    )
    format_type = forms.ChoiceField(
        choices=[('json', 'JSON'), ('csv', 'CSV'), ('excel', 'Excel')],
        initial='json',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    include_responses = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Inclure les réponses dans l'exportation"
    )
