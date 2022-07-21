from django.db import models


class Channel(models.Model):
    name = models.TextField(blank=False, null=False)
    tg_id = models.IntegerField(null=False, unique=True)


class VisitedChannel(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    visited = models.DateTimeField(null=False)


class ChannelMessage(models.Model):
    tg_id = models.IntegerField(null=False, unique=True)
    text = models.TextField(null=False, blank=False)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)


class Forward(models.Model):
    message = models.ForeignKey(ChannelMessage, on_delete=models.CASCADE)
    source = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='forwards')
    target = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='+')
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["message", "source", "target"],
                name="forward_is_unique")]
