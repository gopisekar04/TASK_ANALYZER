from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class Task(models.Model):
    title = models.CharField(max_length=200)
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)]
    )

    importance = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    dependencies = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.title} (#{self.id})"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date,
            "estimated_hours": self.estimated_hours,
            "importance": self.importance,
            "dependencies": self.dependencies or []
        }