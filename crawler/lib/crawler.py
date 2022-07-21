import logging
from asgiref.sync import sync_to_async
from crawler.models import (
  Channel, ChannelMessage, VisitedChannel, Forward
)
from telethon import TelegramClient
from telethon.tl.types import Channel as TgChannel
from telegraph.settings import VISITED_TTL
from django.utils import timezone
from telethon.errors.rpcerrorlist import ChannelPrivateError
import random


class Crawler(object):
    def __init__(self, tg_cli: TelegramClient):
        self._tg_cli = tg_cli
        self._log = logging.getLogger(__name__)

    async def visited_recently(self, channel_id):
        last_visited = await sync_to_async(VisitedChannel\
            .objects.filter(channel__tg_id=channel_id)\
            .order_by('-visited')\
            .first)()
        if last_visited is None:
            return False
        return (
            timezone.now() - last_visited.visited
        ) < VISITED_TTL


    async def visit_channel(self, channel_id, depth=100):
        visited = await self.visited_recently(channel_id)
        if visited:
            self._log.info(f'Channel {channel_id} visited recently, ignore it')
            return [], None
        results = []
        tg_channel = await self._tg_cli.get_entity(channel_id)
        channel, _ = await sync_to_async(Channel.objects.get_or_create)(
            tg_id=tg_channel.id, defaults=dict(name=tg_channel.title))
        async for tg_message in self._tg_cli.iter_messages(channel_id, limit=depth):
            forward = None
            if tg_message.text is None:
                self._log.warn('Message is empty, ignore')
                continue
            message, _ = await sync_to_async(ChannelMessage.objects.get_or_create)(
                tg_id=tg_message.id,
                defaults=dict(text = tg_message.text, channel=channel))
            if tg_message.forward:
                source = tg_message.forward.chat_id
                if source is None:
                    continue
                try:
                    entry_source = await self._tg_cli.get_entity(source)
                except ChannelPrivateError:
                    self._log.warn('Encountered repost to a private channel, ignore')
                    continue
                if isinstance(entry_source, TgChannel):
                    forwarded_from, _ = await sync_to_async(Channel.objects.get_or_create)(
                        tg_id=entry_source.id, defaults=dict(name=entry_source.title))
                    forward, created = await sync_to_async(
                        Forward.objects.get_or_create)(message=message, source=forwarded_from, target=channel)
                    if created:
                        self._log.info(f'Edge added {forward.source.name}->{forward.target.name}')
                    else:
                        self._log.debug('Edge exists')

            results.append((channel, message, forward))
        v = VisitedChannel(channel=channel, visited=timezone.now())
        await sync_to_async(v.save)()
        return results, v


    async def visit_bfs(self, channels, depth=100, steps=10, random_walk=False):
        step = 0
        queue = channels
        visited = []
        while len(queue) > 0 and step < steps:
            channel = queue.pop(
                random.randint(0, len(queue)-1) if random_walk else 0)
            self._log.info(f'Visiting {channel}')
            step += 1
            edges, v = await self.visit_channel(channel, depth=depth)
            if v is not None:
                visited.append(v)
            for _, _, edge in edges:
                if edge is None:
                    continue
                if not await self.visited_recently(edge.source.tg_id):
                    queue.append(edge.source.tg_id)
                else:
                    self._log.info(f'Channel {edge.source.tg_id} visited recently, ignore it')
        return visited

        