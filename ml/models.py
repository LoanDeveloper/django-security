from django.db import models
from django.utils import timezone


class IndexManifest(models.Model):
    """Manifest pour versionner les index vectoriels"""
    name = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=timezone.now)
    file_path = models.CharField(max_length=500)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class SearchLog(models.Model):
    """Journal des recherches pour traçabilité"""
    trace_id = models.UUIDField(unique=True)
    query = models.TextField()
    results_count = models.IntegerField()
    top_k_scores = models.JSONField(default=list)
    index_version = models.CharField(max_length=50)
    response_time_ms = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
