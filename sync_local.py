"""
Local Sync Agent - Keeps your laptop's JARVIS synced with the cloud brain.
Run this alongside the cloud JARVIS to sync local changes.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path

import websockets

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('JARVIS.sync_local')

# Cloud JARVIS WebSocket URL
CLOUD_URL = "ws://localhost:8080/ws"  # Change to your Render URL when deployed


async def check_sync_status():
    """Check the current sync status from cloud JARVIS"""
    try:
        async with websockets.connect(CLOUD_URL) as ws:
            await ws.send(json.dumps({
                'type': 'command',
                'text': 'sync status'
            }))
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(response)
            return data.get('text', 'No response')
    except Exception as e:
        logger.error(f"Failed to check sync status: {e}")
        return None


async def trigger_sync():
    """Trigger a manual sync with cloud JARVIS"""
    try:
        async with websockets.connect(CLOUD_URL) as ws:
            await ws.send(json.dumps({
                'type': 'command',
                'text': 'sync now'
            }))
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(response)
            return data.get('text', 'Sync triggered')
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        return None


async def sync_loop(interval=30):
    """Background sync loop - checks for updates periodically"""
    logger.info(f"Starting local sync loop (interval: {interval}s)")
    
    while True:
        try:
            status = await check_sync_status()
            if status:
                logger.info(f"Sync status: {status[:100]}...")
            
            await asyncio.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Sync loop stopped by user")
            break
        except Exception as e:
            logger.error(f"Sync loop error: {e}")
            await asyncio.sleep(interval)


def main():
    """Main entry point for local sync agent"""
    print("=" * 50)
    print("  JARVIS Local Sync Agent")
    print("=" * 50)
    print(f"Cloud URL: {CLOUD_URL}")
    print("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(sync_loop(interval=30))
    except KeyboardInterrupt:
        print("\nSync agent stopped.")


if __name__ == "__main__":
    main()
