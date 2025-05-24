from django.db import models
from django.contrib.auth.models import User
from surveys.models import Survey, Question, QuestionOption

class SurveyResponse(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='survey_responses')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Réponse au sondage"
        verbose_name_plural = "Réponses aux sondages"
        ordering = ['-submitted_at']
    
    def __str__(self):
        user_str = self.user.username if self.user else "Anonyme"
        return f"Réponse de {user_str} pour {self.survey.title}"

class Answer(models.Model):
    survey_response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE, null=True, blank=True, related_name='answers')
    text_answer = models.TextField(blank=True, null=True, verbose_name="Réponse texte")
    scale_answer = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Réponse échelle")
    
    class Meta:
        verbose_name = "Réponse"
        verbose_name_plural = "Réponses"
    
    def __str__(self):
        return f"Réponse à {self.question.text[:30]}..."
    
    def get_answer_value(self):
        """Retourne la valeur de la réponse en fonction du type de question"""
        if self.question.question_type == 'single' or self.question.question_type == 'multiple':
            return self.selected_option.text if self.selected_option else None
        elif self.question.question_type == 'text':
            return self.text_answer
        elif self.question.question_type == 'scale':
            return self.scale_answer
        return None
