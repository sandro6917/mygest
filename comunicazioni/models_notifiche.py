from django.db import models
from django.utils import timezone

class NotificaInvio(models.Model):
    comunicazione = models.ForeignKey('comunicazioni.Comunicazione', on_delete=models.CASCADE, related_name='notifiche')
    destinatario = models.EmailField()
    stato = models.CharField(max_length=20, choices=[('inviata','Inviata'),('errore','Errore'),('letta','Letta')], default='inviata')
    data_invio = models.DateTimeField(default=timezone.now)
    data_lettura = models.DateTimeField(null=True, blank=True)
    errore = models.TextField(blank=True)

    class Meta:
        verbose_name = "Notifica invio comunicazione"
        verbose_name_plural = "Notifiche invio comunicazioni"
        ordering = ["-data_invio"]

    def __str__(self):
        return f"{self.comunicazione} -> {self.destinatario} [{self.stato}]"
