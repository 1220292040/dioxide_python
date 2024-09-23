import os,sys
sys.path.append('.')

import asyncio
from client.dioxclient import DioxClient


client = DioxClient()
asyncio.get_event_loop().run_until_complete(client.subscribe("transaction_block"))