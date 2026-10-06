from django.db import models


class Project(models.Model):
    title = models.CharField(max_length=120)
    thumbnail = models.ImageField(upload_to="projects/")
    link = models.URLField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
