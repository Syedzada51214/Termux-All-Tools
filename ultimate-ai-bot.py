import os
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Type, Any
from abc import ABC, abstractmethod
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
    JobQueue
)
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
SPORTS_API_KEY = os.getenv('SPORTS_API_KEY')
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
ADMIN_IDS = json.loads(os.getenv('ADMIN_IDS', '[]'))

# Max message length for Telegram
MAX_MESSAGE_LENGTH = 4096

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Plugin Base Class
class PluginBase(ABC):
    """Base class for all plugins"""
    
    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """Return the plugin's name"""
        pass
    
    @classmethod
    @abstractmethod
    def get_commands(cls) -> Dict[str, Any]:
        """Return dict of commands with handlers and descriptions"""
        pass
    
    @abstractmethod
    async def initialize(self, bot: 'TelegramBot') -> None:
        """Initialize plugin with bot instance"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up resources"""
        pass

# ======================
# CORE PLUGINS
# ======================

class WeatherPlugin(PluginBase):
    """Weather information plugin"""
    
    @classmethod
    def get_name(cls) -> str:
        return "weather"
    
    @classmethod
    def get_commands(cls) -> Dict[str, Any]:
        return {
            'weather': {
                'handler': cls.handle_weather,
                'description': 'Get weather for location (e.g. /weather London)',
                'admin_only': False
            }
        }
    
    async def initialize(self, bot: 'TelegramBot') -> None:
        self.bot = bot
        
    async def get_weather(self, location: str) -> str:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={location}"
        try:
            response = requests.get(url)
            data = response.json()
            current = data['current']
            return (
                f"🌤 Weather in {location}:\n"
                f"🌡 Temp: {current['temp_c']}°C\n"
                f"💧 Humidity: {current['humidity']}%\n"
                f"🌬 Wind: {current['wind_kph']} km/h\n"
                f"☁️ {current['condition']['text']}"
            )
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return "⚠️ Could not fetch weather data"
    
    @classmethod
    async def handle_weather(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        plugin = cls()
        location = ' '.join(context.args)
        if not location:
            await update.message.reply_text("Please specify a location (e.g. /weather London)")
            return
        weather_info = await plugin.get_weather(location)
        await update.message.reply_text(weather_info)

# ======================
# PRODUCTIVITY PLUGINS  
# ======================

class ReminderPlugin(PluginBase):
    """Reminder system plugin"""
    
    @classmethod
    def get_name(cls) -> str:
        return "reminder"
    
    @classmethod
    def get_commands(cls) -> Dict[str, Any]:
        return {
            'remind': {
                'handler': cls.handle_reminder,
                'description': 'Set reminder (e.g. /remind call mom in 2 hours)',
                'admin_only': False
            },
            'reminders': {
                'handler': cls.handle_list_reminders,
                'description': 'List your active reminders',
                'admin_only': False
            }
        }
    
    async def initialize(self, bot: 'TelegramBot') -> None:
        self.bot = bot
        self.reminders = {}
        
    async def create_reminder(self, user_id: int, text: str, when: datetime):
        """Schedule reminder using job queue"""
        async def callback(context: ContextTypes.DEFAULT_TYPE):
            await context.bot.send_message(
                chat_id=user_id,
                text=f"⏰ Reminder: {text}"
            )
            del self.reminders[f"{user_id}_{text}"]
            
        delay = (when - datetime.now()).total_seconds()
        job = self.bot.app.job_queue.run_once(callback, delay, chat_id=user_id)
        self.reminders[f"{user_id}_{text}"] = job
        
    @classmethod
    async def handle_reminder(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        plugin = cls()
        user_id = update.effective_user.id
        args = ' '.join(context.args)
        
        try:
            # Simple parsing - would use NLP in production
            parts = args.split(' in ')
            if len(parts) < 2:
                raise ValueError("Invalid format")
                
            text = parts[0].strip()
            time_str = parts[1].strip()
            
            # Convert time string to datetime
            if 'hour' in time_str:
                hours = int(time_str.split()[0])
                when = datetime.now() + timedelta(hours=hours)
            elif 'minute' in time_str:
                minutes = int(time_str.split()[0])
                when = datetime.now() + timedelta(minutes=minutes)
            else:
                raise ValueError("Invalid time format")
                
            await plugin.create_reminder(user_id, text, when)
            await update.message.reply_text(
                f"✅ Reminder set for {when.strftime('%Y-%m-%d %H:%M')}"
            )
            
        except Exception as e:
            logger.error(f"Reminder error: {e}")
            await update.message.reply_text(
                "⚠️ Format: /remind [text] in [number] [minutes|hours]\n"
                "Example: /remind call mom in 2 hours"
            )

# ======================
# FINANCE PLUGINS
# ======================

class CryptoPlugin(PluginBase):
    """Cryptocurrency price tracking"""
    
    @classmethod
    def get_name(cls) -> str:
        return "crypto"
    
    @classmethod
    def get_commands(cls) -> Dict[str, Any]:
        return {
            'crypto': {
                'handler': cls.handle_crypto,
                'description': 'Get crypto price (e.g. /crypto BTC)',
                'admin_only': False
            }
        }
    
    async def initialize(self, bot: 'TelegramBot') -> None:
        self.bot = bot
        
    async def get_crypto_price(self, coin: str) -> str:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        try:
            response = requests.get(url)
            price = response.json()[coin]['usd']
            return f"💰 {coin.upper()}: ${price:,.2f}"
        except Exception as e:
            logger.error(f"Crypto API error: {e}")
            return f"⚠️ Could not fetch {coin} price"
    
    @classmethod
    async def handle_crypto(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        plugin = cls()
        coin = context.args[0].lower() if context.args else 'bitcoin'
        price_info = await plugin.get_crypto_price(coin)
        await update.message.reply_text(price_info)

# ======================
# MAIN BOT APPLICATION  
# ======================

class TelegramBot:
    def __init__(self):
        self.config = {
            'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
            'OPENAI_API_KEY': OPENAI_API_KEY,
            'ADMIN_IDS': ADMIN_IDS
        }
        
        self.app = Application.builder().token(self.config['TELEGRAM_TOKEN']).build()
        self.plugins: Dict[str, PluginBase] = {}
        
        # Register core commands
        self.app.add_handler(CommandHandler("start", self.handle_start))
        self.app.add_handler(CommandHandler("help", self.handle_help))
    
    async def initialize(self):
        """Initialize and load all plugins"""
        self.plugins = {
            'weather': WeatherPlugin(),
            'reminder': ReminderPlugin(),
            'crypto': CryptoPlugin()
        }
        
        # Initialize plugins
        for name, plugin in self.plugins.items():
            await plugin.initialize(self)
            logger.info(f"Initialized plugin: {name}")
            
        # Register plugin commands
        for plugin in self.plugins.values():
            for cmd, info in plugin.get_commands().items():
                self.app.add_handler(CommandHandler(cmd, info['handler']))
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "🤖 Welcome to Ultimate AI Bot!\n"
            "Type /help to see available commands."
        )
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = "🛠 Available Commands:\n\n"
        
        for plugin in self.plugins.values():
            for cmd, info in plugin.get_commands().items():
                if info['admin_only'] and str(update.effective_user.id) not in ADMIN_IDS:
                    continue
                help_text += f"/{cmd} - {info['description']}\n"
        
        await update.message.reply_text(help_text)
    
    async def run(self):
        """Run the bot until stopped"""
        await self.initialize()
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        # Keep running
        while True:
            await asyncio.sleep(1)

# Start the bot
if __name__ == '__main__':
    import asyncio
    bot = TelegramBot()
    asyncio.run(bot.run())
