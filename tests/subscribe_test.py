import sys,time,threading
sys.path.append('.')
from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.types import SubscribeTopic
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
for topic in [SubscribeTopic.CONSENSUS_HEADER,SubscribeTopic.TRANSACTION_BLOCK]:
    t = threading.Thread(target=client.subscribe, args=(topic, handler, None))
    threads.append(t)
    t.start()

start = time.time()

while True:
    print("main thread => pause...")
    time.sleep(1)
    if time.time() - start > 10:
        client.unsubscribe(threads[1].ident)


##test height_filter
# client.subscribe_block_with_height(SubscribeTopic.CONSENSUS_HEADER,10,20)
# client.subscribe_block_with_height(SubscribeTopic.TRANSACTION_BLOCK,20,30)


##test dapp_filter
# client.subscribe_state_with_dapp("00Dapp")

##test contract_filter
# client.subscribe_state_with_contract("00Dapp.Bank")

##test scopekey_filter
# client.subscribe_state_with_scpoekey("4xfx62hjky7yy7x73f7g64ejf5cxjhzhrp8qmb2vnw5y6ms3zgt06zmcpr:ed25519")

##test contract_scopekey_filter
# client.subscribe_state_with_contract_and_scopekey("00Dapp.Bank","qq9bectyb1bpta7z77v7x5pqh1qng44s62bc1gjr653s35e6sgav6gmjg4:ed25519")

##test contract_statekey_filter
# client.subscribe_state_with_contract_and_statekey("core.coin","TotalSupply")

# while True:
#     time.sleep(1)


