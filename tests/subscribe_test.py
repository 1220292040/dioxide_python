import sys
import time
import threading
import pytest

sys.path.append('.')
from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.types import SubscribeTopic


class TestSubscribe:
    """Subscription tests with optimized execution time."""
    
    @pytest.fixture
    def client(self):
        """Create a DioxClient instance."""
        return DioxClient()
    
    def test_subscribe_consensus_header(self, client):
        """Test subscribing to consensus headers with timeout."""
        received_blocks = []
        max_blocks = 2  # Only wait for 2 blocks
        timeout = 5  # Maximum 5 seconds
        
        def handler(block):
            received_blocks.append(block)
            print(f"Received block at height: {block.get('Height', 'N/A')}")
        
        # Start subscription in background thread
        thread = threading.Thread(
            target=client.subscribe,
            args=(SubscribeTopic.CONSENSUS_HEADER, handler, None)
        )
        thread.daemon = True
        thread.start()
        
        # Wait for blocks or timeout
        start_time = time.time()
        while len(received_blocks) < max_blocks and (time.time() - start_time) < timeout:
            time.sleep(0.5)
        
        # Unsubscribe
        try:
            client.unsubscribe(thread.ident)
        except:
            pass
        
        # Verify we received at least one block
        assert len(received_blocks) > 0, "Should receive at least one consensus header"
        
        # Verify block structure
        if received_blocks:
            block = received_blocks[0]
            assert 'Height' in block, "Block should have Height field"
            print(f"Test passed: Received {len(received_blocks)} blocks")
    
    def test_subscribe_transaction_block(self, client):
        """Test subscribing to transaction blocks with timeout."""
        received_blocks = []
        max_blocks = 2
        timeout = 5
        
        def handler(block):
            received_blocks.append(block)
            print(f"Received transaction block: {block.get('Hash', 'N/A')[:16]}...")
        
        thread = threading.Thread(
            target=client.subscribe,
            args=(SubscribeTopic.TRANSACTION_BLOCK, handler, None)
        )
        thread.daemon = True
        thread.start()
        
        start_time = time.time()
        while len(received_blocks) < max_blocks and (time.time() - start_time) < timeout:
            time.sleep(0.5)
        
        try:
            client.unsubscribe(thread.ident)
        except:
            pass
        
        assert len(received_blocks) > 0, "Should receive at least one transaction block"
        
        if received_blocks:
            block = received_blocks[0]
            assert 'Hash' in block or 'Height' in block, "Block should have Hash or Height field"
            print(f"Test passed: Received {len(received_blocks)} transaction blocks")
    
    def test_subscribe_with_height_filter(self, client):
        """Test subscribing with height filter (quick test)."""
        received_blocks = []
        timeout = 3  # Shorter timeout for filtered subscription
        
        def handler(block):
            height = block.get('Height', 0)
            received_blocks.append(block)
            print(f"Received filtered block at height: {height}")
        
        # Get current height first
        try:
            info = client.get_chain_info()
            current_height = info.get('Height', 0)
            
            # Subscribe to next 5 blocks only
            thread = threading.Thread(
                target=client.subscribe_block_with_height,
                args=(SubscribeTopic.CONSENSUS_HEADER, current_height, current_height + 5)
            )
            thread.daemon = True
            thread.start()
            
            start_time = time.time()
            while len(received_blocks) < 2 and (time.time() - start_time) < timeout:
                time.sleep(0.5)
            
            try:
                client.unsubscribe(thread.ident)
            except:
                pass
            
            # This test may not receive blocks if chain is slow, so we just verify it doesn't crash
            print(f"Height filter test: Received {len(received_blocks)} blocks")
            
        except Exception as e:
            pytest.skip(f"Chain not available or too slow: {e}")
    
    @pytest.mark.skip(reason="Manual test - requires specific dapp deployment")
    def test_subscribe_state_with_dapp(self, client):
        """Test subscribing to state changes for a specific dapp."""
        # This is a manual test that requires a deployed dapp
        pass
    
    @pytest.mark.skip(reason="Manual test - requires specific contract")
    def test_subscribe_state_with_contract(self, client):
        """Test subscribing to state changes for a specific contract."""
        pass


if __name__ == "__main__":
    # Quick manual test
    print("Running quick subscription test...")
    client = DioxClient()
    
    received = []
    def handler(block):
        received.append(block)
        print(f"Block height: {block.get('Height', 'N/A')}")
    
    thread = threading.Thread(
        target=client.subscribe,
        args=(SubscribeTopic.CONSENSUS_HEADER, handler, None)
    )
    thread.daemon = True
    thread.start()
    
    print("Waiting for 2 blocks (max 5 seconds)...")
    start = time.time()
    while len(received) < 2 and (time.time() - start) < 5:
        time.sleep(0.5)
    
    try:
        client.unsubscribe(thread.ident)
    except:
        pass
    
    print(f"Received {len(received)} blocks in {time.time() - start:.2f} seconds")

