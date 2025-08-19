"""Telegram Bot runner script với proper error handling"""

import asyncio
import sys
import os
import logging
from typing import Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.integrations.telegram.bot import TelegramBot
from src.config import settings
from src.logging_config import setup_logging
from src.core.exceptions import IntegrationException

logger = logging.getLogger(__name__)

class TelegramBotRunner:
    """
    Runner class cho Telegram Bot
    Separation of Concerns: Handle bot lifecycle
    """
    
    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.bot: Optional[TelegramBot] = None
        
        if not self.bot_token:
            raise IntegrationException("TELEGRAM_BOT_TOKEN environment variable required")
    
    async def run(self):
        """Run bot với proper error handling"""
        try:
            # Setup logging
            setup_logging()
            logger.info("Starting Telegram Bot Runner...")
            
            # Validate bot token
            if len(self.bot_token) < 20:
                raise IntegrationException("Invalid Telegram bot token")
            
            # Initialize bot
            self.bot = TelegramBot(self.bot_token)
            await self.bot.initialize()
            
            # Start polling
            logger.info("Bot initialized successfully, starting polling...")
            await self.bot.start_polling()
            
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except IntegrationException as e:
            logger.error(f"Integration error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.bot:
            logger.info("Shutting down bot...")
            await self.bot.stop()
        
        logger.info("Cleanup completed")

def main():
    """Main entry point"""
    runner = TelegramBotRunner()
    
    try:
        asyncio.run(runner.run())
    except KeyboardInterrupt:
        print("\\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()