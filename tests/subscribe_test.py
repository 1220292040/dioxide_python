import sys,time,threading
sys.path.append('.')
from dioxide_python_sdk.client.dioxclient import DioxClient

def handler(r):
    print(r)

def filter1(r):
    if r["Height"] > 10 and r["Height"]<20:
        return True
    else:
        return False

def filter2(r):
    if r["Height"] > 20:
        return True
    else:
        return False

client = DioxClient()


threads = []
for topic in ["consensus_header", "transaction_block"]:
    t = threading.Thread(target=client.subscribe, args=(topic, handler, None))
    threads.append(t)
    t.start()

start = time.time()

while True:
    print("main thread => pause...")
    time.sleep(1)
    if time.time() - start > 10:
        client.unsubscribe(threads[1].ident)


