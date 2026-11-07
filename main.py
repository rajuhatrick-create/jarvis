"""
JARVIS - Just A Rather Very Intelligent System
A local AI assistant with voice control, system management, and web interface.
"""

import os
import sys
import yaml
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('JARVIS')

# Project root
PROJECT_ROOT = Path(__file__).parent

def load_config():
    """Load configuration from config.yaml, with environment variable overrides"""
    config_path = PROJECT_ROOT / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Allow environment variables to override config (for Render deployment)
    env_mode = os.environ.get('JARVIS_MODE')
    if env_mode:
        config['mode'] = env_mode
        logger.info(f"Mode overridden by environment: {env_mode}")
    
    env_port = os.environ.get('PORT')
    if env_port:
        config['server']['port'] = int(env_port)
        logger.info(f"Port overridden by environment: {env_port}")
    
    env_db_path = os.environ.get('DATABASE_PATH')
    if env_db_path:
        config['database']['path'] = env_db_path
        config['database']['enabled'] = True
        logger.info(f"Database path overridden by environment")
    
    return config

def main():
    """Main entry point for JARVIS"""
    logger.info("Initializing JARVIS...")
    
    # Load configuration
    config = load_config()
    logger.info(f"Configuration loaded from {PROJECT_ROOT / 'config.yaml'}")
    
    # Ensure database directory exists (e.g., OneDrive path)
    db_path = Path(config.get('database', {}).get('path', 'data/jarvis.db'))
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created database directory: {db_path.parent}")
    
    # Detect mode
    mode = config.get('mode', 'local')
    logger.info(f"Running in {mode} mode")
    
    # Start the web server
    from jarvis.ui.server import create_app
    import uvicorn
    
    app = create_app(config)
    
    host = config['server']['host']
    port = config['server']['port']
    
    logger.info(f"Starting JARVIS on http://{host}:{port}")
    if mode == 'local':
        print(f"\n{'='*50}")
        print(f"  JARVIS is running at http://localhost:{port}")
        print(f"  Mode: {mode}")
        print(f"{'='*50}\n")
    else:
        logger.info(f"JARVIS cloud mode running on port {port}")
    
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
