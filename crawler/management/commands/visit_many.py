from cmath import log
from django.core.management.base import BaseCommand
from crawler.lib.crawler import Crawler
from crawler.models import Channel, VisitedChannel
from telegraph.settings import VISITED_TTL
from django.utils import timezone 
import asyncio
import logging
from telethon import TelegramClient
from telegraph.settings import CRAWLER_SESSION
from asgiref.sync import sync_to_async


log = logging.getLogger(__name__)


def _channels_to_visit(count):
    not_visited_channels = Channel.objects.filter(
        visitedchannel__isnull=True).all()
    channels = list({x.tg_id for x in not_visited_channels})[:count]
    channels_not_visited_recently = VisitedChannel\
        .objects\
        .filter(visited__lte=timezone.now() - VISITED_TTL)\
        .all()
    visited_channels = list({
        x.channel.tg_id for x in channels_not_visited_recently})[:count]
    channels = [x for x in list(set(channels) | set(visited_channels))[:count]]
    for channel in Channel.objects.filter(tg_id__in=channels):
        log.info(f'Going to visit channel {channel.name}/{channel.tg_id}')
    return channels

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('channel', nargs='*')
        parser.add_argument('--api-id')
        parser.add_argument('--api-hash')
        parser.add_argument('--id', action='store_true', default=False)
        parser.add_argument('--random', action='store_true', default=False)
        parser.add_argument('--steps', type=int, default=10)
        parser.add_argument('--messages', type=int, default=100)


    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        async def do_handle():
            async with TelegramClient(CRAWLER_SESSION, api_hash=options['api_hash'],
                                      api_id=options['api_id']) as c:
                crawler = Crawler(c)

                channels = None
                if len(options['channel']) == 0 or options['channel'] is None:
                    options['id'] = True
                    channels = await sync_to_async(_channels_to_visit)(options['steps'])
                else:
                    channels = options['channel']

                assert channels is not None
                channel_ids = []
                for channel_name_or_id in channels:
                    if not options['id']:
                        channel_name = channel_name_or_id
                        channel = await c.get_entity(channel_name)
                        log.info(f'Channel {channel_name} has id {channel.id}')
                        channel_ids.append(channel.id)
                    else:
                        channel_id = int(channel_name_or_id)
                        channel_ids.append(channel_id)
                visited = await crawler.visit_bfs(
                    channel_ids, depth=options['messages'], steps=options['steps'],
                    random_walk=options['random'])
                return visited
        visited = loop.run_until_complete(do_handle())
        for v in visited:
            log.info(f'Visited {v.channel.name}/{v.channel.tg_id}')

        