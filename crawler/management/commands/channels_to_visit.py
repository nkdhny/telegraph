from django.core.management.base import BaseCommand
from crawler.models import Channel, VisitedChannel
from django.utils import timezone
from telegraph.settings import VISITED_TTL

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('count', type=int)

    def handle(self, *args, **options):
        channels = {x.tg_id for x in Channel.objects.filter(
            visitedchannel__isnull=True).all()[:options['count']]}
        visited_channels = {x.channel.tg_id for x in VisitedChannel\
            .objects\
            .filter(visited__lte=timezone.now() - VISITED_TTL)\
            .all()[:options['count']]}
        channels = [str(x) for x in list(channels | visited_channels)[:options['count']]]
        print(' '.join(channels))
