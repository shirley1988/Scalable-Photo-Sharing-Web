from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Photos(models.Model):
    user = models.ForeignKey(User, to_field='username')
    s3_key = models.CharField(max_length=64)
    description = models.CharField(max_length=256)
    category = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 's3_key',)
