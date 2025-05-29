#!/usr/bin/env python
"""
Script to update the bot configuration files to use the test database.

This script updates the SQLQueryTool configuration in all bot configuration files
to use the test database.
"""

import os
import sys
import yaml
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test database path
TEST_DB_PATH = os.path.abspath("test_db.sqlite")
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs")


def update_configs():
    """Update the bot configuration files to use the test database."""
    # Check if the test database exists
    if not os.path.exists(TEST_DB_PATH):
        logger.error(f"Test database not found at {TEST_DB_PATH}. Please run create_test_db.py first.")
        return False
    
    # Get all YAML files in the configs directory
    config_files = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".yaml")]
    
    if not config_files:
        logger.error(f"No configuration files found in {CONFIG_DIR}")
        return False
    
    # Update each configuration file
    for config_file in config_files:
        config_path = os.path.join(CONFIG_DIR, config_file)
        logger.info(f"Updating configuration file: {config_path}")
        
        # Load the configuration
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # Check if the configuration has tools
        if "tools" not in config:
            logger.warning(f"No tools found in {config_file}")
            continue
        
        # Find the SQLQueryTool
        updated = False
        for tool in config["tools"]:
            if tool["type"] == "SQLQueryTool" and tool["enabled"]:
                # Update the connection string
                tool["config"]["connection_string"] = f"sqlite:///{TEST_DB_PATH}"
                updated = True
                logger.info(f"Updated SQLQueryTool in {config_file}")
        
        # Update the database section if it exists
        if "database" in config and "sql" in config["database"]:
            config["database"]["sql"]["connection_string"] = f"sqlite:///{TEST_DB_PATH}"
            updated = True
            logger.info(f"Updated database.sql in {config_file}")
        
        # Save the updated configuration
        if updated:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Saved updated configuration to {config_path}")
        else:
            logger.warning(f"No SQLQueryTool found in {config_file}")
    
    return True


if __name__ == "__main__":
    success = update_configs()
    
    if success:
        print(f"Configuration files updated to use test database at: {TEST_DB_PATH}")
    else:
        print("Failed to update configuration files. Check the logs for details.")
