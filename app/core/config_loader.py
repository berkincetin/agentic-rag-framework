"""
Configuration loading utilities for the Agentic RAG system.
"""
import os
import yaml
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

from app.models.bot_config import BotConfig

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Utility class for loading bot configurations."""
    
    def __init__(self, config_dir: str = "configs"):
        """
        Initialize the config loader.
        
        Args:
            config_dir: Directory containing bot configuration files
        """
        self.config_dir = config_dir
        self.configs: Dict[str, BotConfig] = {}
        self._load_configs()
    
    def _load_configs(self) -> None:
        """Load all configuration files from the config directory."""
        config_path = Path(self.config_dir)
        if not config_path.exists():
            logger.warning(f"Config directory {self.config_dir} does not exist")
            return
        
        for file_path in config_path.glob("*.yaml"):
            try:
                with open(file_path, "r") as f:
                    config_data = yaml.safe_load(f)
                
                bot_config = BotConfig(**config_data)
                self.configs[bot_config.name] = bot_config
                logger.info(f"Loaded configuration for bot: {bot_config.name}")
            except Exception as e:
                logger.error(f"Error loading config from {file_path}: {str(e)}")
    
    def get_config(self, bot_name: str) -> Optional[BotConfig]:
        """
        Get the configuration for a specific bot.
        
        Args:
            bot_name: Name of the bot
            
        Returns:
            The bot configuration or None if not found
        """
        return self.configs.get(bot_name)
    
    def get_all_configs(self) -> Dict[str, BotConfig]:
        """
        Get all bot configurations.
        
        Returns:
            Dictionary of bot configurations
        """
        return self.configs
    
    def reload_configs(self) -> None:
        """Reload all configuration files."""
        self.configs = {}
        self._load_configs()
    
    def load_prompt(self, prompt_path: str) -> str:
        """
        Load a prompt template from a file.
        
        Args:
            prompt_path: Path to the prompt template file
            
        Returns:
            The prompt template as a string
        """
        try:
            with open(prompt_path, "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading prompt from {prompt_path}: {str(e)}")
            return ""
