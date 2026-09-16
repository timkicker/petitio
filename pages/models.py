"""petition portal data model"""

from django.db import models


class Account(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    password_hash = models.CharField(max_length=256)
    is_moderator = models.BooleanField(default=False)
    failed_logins = models.IntegerField(default=0)

    def __str__(self) -> str:
        return self.username


class Petition(models.Model):
    owner = models.ForeignKey(Account, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, default="open")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class Signature(models.Model):
    petition = models.ForeignKey(Petition, on_delete=models.CASCADE, related_name="signatures")
    signer_name = models.CharField(max_length=100)
    signer_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    ts = models.DateTimeField(auto_now_add=True)
    actor = models.CharField(max_length=50)
    action = models.CharField(max_length=100)
    target = models.CharField(max_length=200)
    ip = models.CharField(max_length=64)
