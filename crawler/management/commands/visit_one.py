from cmath import log
from django.core.management.base import BaseCommand, CommandError
from django.core.management.base import BaseCommand
from crawler.lib.crawler import Crawler 
import asyncio
import logging
from telethon import TelegramClient
from django.db import transaction
from telegraph.settings import CRAWLER_SESSION


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('channel_name')
        parser.add_argument('--api-id')
        parser.add_argument('--api-hash')

    def handle(self, *args, **options):
        log = logging.getLogger(__name__)
        loop = asyncio.get_event_loop()
        async def do_handle():
            async with TelegramClient(CRAWLER_SESSION, api_hash=options['api_hash'],
                                      api_id=options['api_id']) as c:
                crawler = Crawler(c)
                channel = await c.get_entity(options['channel_name'])
                log.info(f'Visiting {channel.title}/{channel.id}')
                visited = await crawler.visit_channel(channel.id)
                return visited
        with transaction.atomic():
            created = loop.run_until_complete(do_handle())
        log.info(f'Visited {len(created)} messages')
        for _, _, edge in created:
            if edge is None:
                continue
            log.info(f'Edge added {edge.source} -> {edge.target}')

        