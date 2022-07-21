import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import Channel


api_id = 9364473
api_hash = 'bae2d31ee352c151413cee073c02189d'

async def main():
    async with TelegramClient('telegraph_session', api_id, api_hash) as client:
        chat = await client.get_peer_id('rt_russian')
        m = []
        async for message in client.iter_messages(1036362176, limit=10):
            s = None
            e = None
            if message.forward:
                s = message.forward.chat_id
                e = await client.get_entity(s)
            m.append((
                message.peer_id.channel_id, e.id if e else None, f'"{message.text[:10]}..."', isinstance(e, Channel),
                message.id
            ))
        print(await client.get_peer_id(1036362176))
        return m
loop = asyncio.get_event_loop()
print(loop.run_until_complete(main()))

# https://colab.research.google.com/github/ai-forever/ru-gpts/blob/master/examples/Generate_text_with_RuGPTs_HF.ipynb#scrollTo=J4dxChLE_4pK