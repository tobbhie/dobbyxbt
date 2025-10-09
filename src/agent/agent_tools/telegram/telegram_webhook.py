import logging
import asyncio
import aiohttp  
import json
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes 
from src.agent.agent_tools.telegram.telegram_config import TelegramConfig

# Configure logging for Render
import sys
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure logging is properly configured
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.propagate = False

class TelegramWebhook:
    def __init__(self, token, model=None):
        logger.info("[TELEGRAM] Initializing DobbyXBT Bot for Render...")
        self.token = token
        self.model = model
        self.config = TelegramConfig()
        self.application = None
        self.cryptorank_api_key = self.config.CRYPTO_API_KEY
        self.cryptorank_base_url = self.config.CRYPTO_API_BASE_URL
        
        # Initialize AI model if not provided
        if not self.model:
            try:
                from src.agent.agent_tools.model.model import Model
                import os
                model_api_key = os.getenv("MODEL_API_KEY")
                if model_api_key:
                    self.model = Model(model_api_key)
                    logger.info("[TELEGRAM] AI model initialized successfully.")
                else:
                    logger.warning("[TELEGRAM] No MODEL_API_KEY found. Bot will use basic responses.")
            except Exception as e:
                logger.error(f"[TELEGRAM] Failed to initialize AI model: {str(e)}")
                self.model = None
        
        # Validate API key
        if not self.cryptorank_api_key:
            logger.warning("[TELEGRAM] No CryptoRank API key found. Please set CRYPTORANK_API_KEY environment variable.")
            logger.warning("[TELEGRAM] Bot will not be able to fetch real data without an API key.")
        else:
            logger.info("[TELEGRAM] CryptoRank API key loaded from environment variable.")

    def set_api_key(self, api_key: str):
        """Allow users to set their CryptoRank API key at runtime."""
        self.cryptorank_api_key = api_key
        if api_key:
            logger.info("[TELEGRAM] CryptoRank API key updated successfully.")

    def _initialize_handlers_only(self):
        """Initialize handlers without starting the bot (for webhook mode)"""
        from telegram.request import HTTPXRequest
        
        # Create request with timeout settings
        request = HTTPXRequest(
            connection_pool_size=8,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30
        )
        
        # Create application with custom request
        self.application = Application.builder().token(self.token).request(request).build()
        
        # Add handlers - streamlined
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("price", self.price_command))
        self.application.add_handler(CommandHandler("trending", self.trending_command))
        self.application.add_handler(CommandHandler("funds", self.funds_command))
        self.application.add_handler(CommandHandler("drophunting", self.drophunting_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("[TELEGRAM] Handlers initialized for webhook mode")

    async def get_crypto_prices(self, symbol: str = None) -> list:
        """Get cryptocurrency prices from CryptoRank API v2."""
        try:
            if not self.cryptorank_api_key:
                logger.error("[TELEGRAM] No CryptoRank API key provided. Please set CRYPTORANK_API_KEY environment variable or use set_api_key() method.")
                return []
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.cryptorank_base_url}/currencies"
                headers = {
                    'X-Api-Key': self.cryptorank_api_key
                }
                params = {
                    'limit': 20,
                    'sortBy': 'marketCap',
                    'sortDirection': 'DESC'
                }
                if symbol:
                    params['symbol'] = symbol.upper()
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if not data or 'data' not in data:
                                logger.warning("[TELEGRAM] No data in API response")
                                return []
                            
                            prices = []
                            for currency in data.get('data', []):
                                try:
                                    price = float(currency.get('price', 0)) if currency.get('price') else 0
                                    change_24h = float(currency.get('change24h', 0)) if currency.get('change24h') else 0
                                    market_cap = float(currency.get('marketCap', 0)) if currency.get('marketCap') else 0
                                    
                                    prices.append({
                                        'symbol': currency.get('symbol', 'Unknown'),
                                        'name': currency.get('name', 'Unknown'),
                                        'price': price,
                                        'change_24h': change_24h,
                                        'market_cap': market_cap,
                                        'rank': currency.get('rank', 0)
                                    })
                                except (ValueError, TypeError) as e:
                                    logger.warning(f"[TELEGRAM] Error parsing currency data: {e}")
                                    continue
                            return prices
                        except Exception as e:
                            logger.error(f"[TELEGRAM] Error parsing API response: {e}")
                            return []
                    else:
                        error_text = await response.text()
                        logger.error(f"[TELEGRAM] CryptoRank API error: {response.status} - {error_text}")
                        return []
        except Exception as e:
            logger.error(f"[TELEGRAM] Error fetching crypto prices: {str(e)}")
            return []

    async def get_trending_crypto(self, trend_type: str = "marketCap") -> list:
        """Get trending cryptocurrencies from CryptoRank API v2."""
        try:
            if not self.cryptorank_api_key:
                logger.error("[TELEGRAM] No CryptoRank API key provided. Please set CRYPTORANK_API_KEY environment variable or use set_api_key() method.")
                return []
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.cryptorank_base_url}/currencies"
                headers = {
                    'X-Api-Key': self.cryptorank_api_key
                }
                params = {
                    'limit': 20,
                    'sortBy': trend_type,
                    'sortDirection': 'DESC'
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        trending = []
                        for currency in data.get('data', []):
                            try:
                                price = float(currency.get('price', 0)) if currency.get('price') else 0
                                change_24h = float(currency.get('change24h', 0)) if currency.get('change24h') else 0
                                market_cap = float(currency.get('marketCap', 0)) if currency.get('marketCap') else 0
                                
                                trending.append({
                                    'symbol': currency.get('symbol', 'Unknown'),
                                    'name': currency.get('name', 'Unknown'),
                                    'price': price,
                                    'change_24h': change_24h,
                                    'market_cap': market_cap,
                                    'rank': currency.get('rank', 0)
                                })
                            except (ValueError, TypeError) as e:
                                logger.warning(f"[TELEGRAM] Error parsing trending data: {e}")
                                continue
                        return trending
                    else:
                        logger.error(f"[TELEGRAM] CryptoRank API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"[TELEGRAM] Error fetching trending crypto: {str(e)}")
            return []

    async def get_funds_data(self) -> list:
        """Get investment funds data from CryptoRank API v2."""
        try:
            if not self.cryptorank_api_key:
                logger.error("[TELEGRAM] No CryptoRank API key provided. Please set CRYPTORANK_API_KEY environment variable or use set_api_key() method.")
                return []
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.cryptorank_base_url}/funds/map"
                headers = {
                    'X-Api-Key': self.cryptorank_api_key
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        funds = []
                        for fund in data.get('data', []):
                            funds.append({
                                'name': fund.get('name', 'Unknown'),
                                'type': fund.get('type', 'Unknown'),
                                'tier': fund.get('tier', 'Unknown')
                            })
                        return funds
                    else:
                        logger.error(f"[TELEGRAM] CryptoRank funds API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"[TELEGRAM] Error fetching funds data: {str(e)}")
            return []

    async def get_drophunting_data(self, status: str = None) -> list:
        """Get drophunting activities from CryptoRank API with cheeky 403 error handling."""
        try:
            if not self.cryptorank_api_key:
                logger.error("[TELEGRAM] No CryptoRank API key provided. Please set CRYPTORANK_API_KEY environment variable or use set_api_key() method.")
                return []
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.cryptorank_base_url}/drophunting/activities"
                headers = {
                    'X-Api-Key': self.cryptorank_api_key
                }
                params = {
                    'limit': 10,
                    'sortBy': 'lastStatusUpdate',
                    'sortDirection': 'DESC'
                }
                if status:
                    params['status'] = status
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        activities = []
                        for activity in data.get('data', []):
                            activities.append({
                                'name': activity.get('name', 'Unknown'),
                                'reward_type': activity.get('rewardType', 'Unknown'),
                                'status': activity.get('status', 'Unknown'),
                                'total_raised': activity.get('totalRaised', 0),
                                'x_score': activity.get('xScore', 0),
                                'subscriber_count': activity.get('subscriberCount', 0)
                            })
                        return activities
                    elif response.status == 403:
                        # Cheeky error message for paid API requirement
                        logger.warning("[TELEGRAM] 403 Forbidden - Paid API required for drophunting endpoint")
                        return [{
                            'name': '💸 Developer Too Broke',
                            'reward_type': 'Paid API Required',
                            'status': '403 Forbidden',
                            'total_raised': 0,
                            'x_score': '💸',
                            'subscriber_count': 0,
                            'error_message': 'The developer is too broke to afford the paid version of CryptoRank drophunting API endpoint! 💸'
                        }]
                    else:
                        logger.error(f"[TELEGRAM] CryptoRank drophunting API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"[TELEGRAM] Error fetching drophunting data: {str(e)}")
            return []

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        try:
            welcome_message = (
                "🤖 **Welcome to DobbyXBT Bot!**\n\n"
                "I'm your AI-powered cryptocurrency assistant! 🚀\n\n"
                "**What I can do:**\n"
                "💰 Get real-time crypto prices\n"
                "📈 Show trending cryptocurrencies\n"
                "🏦 Find top crypto investors & funds\n"
                "🎯 Discover airdrop opportunities\n"
                "💬 Chat naturally about crypto\n\n"
                "Created by [pipsandbills](https://x.com/pipsandbills)\n\n"
                "Use /help to see all commands!"
            )
            
            keyboard = [
                [InlineKeyboardButton("💰 Price", callback_data="price_menu")],
                [InlineKeyboardButton("📈 Trending", callback_data="trending_menu")],
                [InlineKeyboardButton("🏦 Funds", callback_data="funds_menu")],
                [InlineKeyboardButton("🎯 Drophunting", callback_data="drophunting_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in start command: {str(e)}")
            await update.message.reply_text("❌ Error starting bot. Please try again.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        try:
            help_text = (
                "🤖 **DobbyXBT Bot Commands**\n\n"
                "**Main Commands:**\n"
                "• /start - Welcome message\n"
                "• /help - Show this help\n\n"
                "**Crypto Commands:**\n"
                "• /price <symbol> - Get crypto price (e.g., /price BTC)\n"
                "• /trending - Top trending cryptocurrencies\n"
                "• /funds - Top crypto investors & funds\n"
                "• /drophunting - Airdrop activities\n\n"
                "**Natural Language:**\n"
                "Just chat naturally! Try:\n"
                "• \"What's the price of Bitcoin?\"\n"
                "• \"Show me trending cryptos\"\n"
                "• \"Top crypto investors\"\n"
                "• \"Any new airdrops?\"\n\n"
                "Created by [pipsandbills](https://x.com/pipsandbills)"
            )
            
            await update.message.reply_text(help_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in help command: {str(e)}")
            await update.message.reply_text("❌ Error showing help. Please try again.")

    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command."""
        try:
            if not update or not update.message:
                logger.error("[TELEGRAM] Invalid update or message in price command")
                return
                
            args = context.args
            if not args:
                await update.message.reply_text("❌ Please provide a cryptocurrency symbol. Example: /price BTC")
                return
            
            symbol = args[0].upper()
            price_data = await self.get_crypto_prices(symbol)
            
            if price_data:
                crypto = price_data[0]
                change_emoji = "📈" if crypto['change_24h'] >= 0 else "📉"
                
                response = f"💰 **{crypto['name']} ({crypto['symbol']})**\n\n"
                response += f"💵 Price: ${crypto['price']:,.2f}\n"
                response += f"{change_emoji} 24h Change: {crypto['change_24h']:+.2f}%\n"
                response += f"🏆 Rank: #{crypto['rank']}\n"
                response += f"💎 Market Cap: ${crypto['market_cap']:,.0f}"
                
                await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ Could not find price for {symbol}. Please check the symbol and try again.")
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in price command: {str(e)}")
            await update.message.reply_text("❌ Error fetching price data. Please try again.")

    async def trending_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trending command."""
        try:
            if not update or not update.message:
                logger.error("[TELEGRAM] Invalid update or message in trending command")
                return
            
            # Show instant feedback
            status_msg = await update.message.reply_text("⏳ Fetching trending data...")
            
            # Process directly without creating tasks
            await self._handle_trending_command_async(update, context, status_msg)
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in trending command: {str(e)}")
            if update and update.message:
                await update.message.reply_text("❌ Error fetching trending data. Please try again.")

    async def _handle_trending_command_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE, status_msg):
        """Handle trending command asynchronously."""
        try:
            trending_data = await self.get_trending_crypto()
            if trending_data:
                response = "🔥 **Top Trending Cryptocurrencies:**\n\n"
                
                for i, crypto in enumerate(trending_data[:10], 1):
                    change_emoji = "📈" if crypto['change_24h'] >= 0 else "📉"
                    response += f"{i}. **{crypto['name']} ({crypto['symbol']})**\n"
                    response += f"   💵 ${crypto['price']:,.2f} {change_emoji} {crypto['change_24h']:+.2f}%\n\n"
                
                await status_msg.edit_text(response, parse_mode='Markdown')
            else:
                await status_msg.edit_text("❌ Could not fetch trending data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable.")
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in trending command async: {str(e)}")
            await status_msg.edit_text("❌ Error fetching trending data. Please try again.")

    async def funds_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /funds command."""
        try:
            if not update or not update.message:
                logger.error("[TELEGRAM] Invalid update or message in funds command")
                return
            
            # Show instant feedback
            status_msg = await update.message.reply_text("⏳ Fetching funds data...")
            
            # Process directly without creating tasks
            await self._handle_funds_command_async(update, context, status_msg)
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in funds command: {str(e)}")
            if update and update.message:
                await update.message.reply_text("❌ Error fetching funds data. Please try again.")

    async def _handle_funds_command_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE, status_msg):
        """Handle funds command asynchronously."""
        try:
            funds_data = await self.get_funds_data()
            if funds_data:
                response = "🏦 **Top Crypto Investment Funds:**\n\n"
                
                for i, fund in enumerate(funds_data[:10], 1):
                    response += f"{i}. **{fund['name']}**\n"
                    response += f"   🏢 Type: {fund['type']}\n"
                    response += f"   ⭐ Tier: {fund['tier']}\n\n"
                
                await status_msg.edit_text(response, parse_mode='Markdown')
            else:
                await status_msg.edit_text("❌ Could not fetch funds data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable.")
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in funds command async: {str(e)}")
            await status_msg.edit_text("❌ Error fetching funds data. Please try again.")

    async def drophunting_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /drophunting command for airdrop activities."""
        try:
            if not update or not update.message:
                logger.error("[TELEGRAM] Invalid update or message in drophunting command")
                return
            
            # Show instant feedback
            status_msg = await update.message.reply_text("⏳ Fetching drophunting data...")
            
            # Process directly without creating tasks
            await self._handle_drophunting_command_async(update, context, status_msg)
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in drophunting command: {str(e)}")
            if update and update.message:
                await update.message.reply_text("❌ Error fetching drophunting data. Please try again.")

    async def _handle_drophunting_command_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE, status_msg):
        """Handle drophunting command asynchronously."""
        try:
            args = context.args
            status = args[0] if args else None
            
            drophunting_data = await self.get_drophunting_data(status)
            if drophunting_data:
                # Check if it's the cheeky error message
                if drophunting_data[0].get('error_message'):
                    response = f"🎯 **Drophunting Activities:**\n\n"
                    response += f"💸 **{drophunting_data[0]['name']}**\n"
                    response += f"   🎁 Reward: {drophunting_data[0]['reward_type']}\n"
                    response += f"   📊 Status: {drophunting_data[0]['status']}\n"
                    response += f"   📱 X Score: {drophunting_data[0]['x_score']}\n\n"
                    response += f"**{drophunting_data[0]['error_message']}**\n\n"
                    response += f"💡 *This endpoint requires a paid CryptoRank API subscription.*"
                else:
                    response = "🎯 **Drophunting Activities:**\n\n"
                    
                    for i, activity in enumerate(drophunting_data[:10], 1):
                        response += f"{i}. **{activity['name']}**\n"
                        response += f"   🎁 Reward: {activity['reward_type']}\n"
                        response += f"   📊 Status: {activity['status']}\n"
                        if activity.get('total_raised'):
                            response += f"   💰 Raised: ${activity['total_raised']:,.0f}\n"
                        response += f"   📱 X Score: {activity.get('x_score', 'N/A')}\n\n"
                
                await status_msg.edit_text(response, parse_mode='Markdown')
            else:
                await status_msg.edit_text("❌ Could not fetch drophunting data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable.")
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in drophunting command async: {str(e)}")
            await status_msg.edit_text("❌ Error fetching drophunting data. Please try again.")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks."""
        try:
            query = update.callback_query
            if not query:
                logger.error("[TELEGRAM] No callback query in update")
                return
                
            await query.answer()
            
            if query.data == "price_menu":
                await query.edit_message_text(
                    "💰 **Price Lookup**\n\n"
                    "Use /price <symbol> to get real-time prices.\n"
                    "Example: /price BTC\n\n"
                    "Supported symbols: BTC, ETH, ADA, SOL, etc.",
                    parse_mode='Markdown'
                )
            elif query.data == "trending_menu":
                # Show instant feedback and process directly
                await query.edit_message_text("⏳ Fetching trending data...")
                await self._handle_trending_async(update, context, query)
            elif query.data == "funds_menu":
                # Show instant feedback and process directly
                await query.edit_message_text("⏳ Fetching funds data...")
                await self._handle_funds_async(update, context, query)
            elif query.data == "drophunting_menu":
                # Show instant feedback and process directly
                await query.edit_message_text("⏳ Fetching drophunting data...")
                await self._handle_drophunting_async(update, context, query)
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in button callback: {str(e)}")

    async def _handle_trending_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Handle trending button press asynchronously."""
        try:
            # Show instant feedback
            await query.edit_message_text("⏳ Fetching trending data...")
            
            # Fetch data
            trending_data = await self.get_trending_crypto()
            
            if trending_data:
                response = "🔥 **Top Trending Cryptocurrencies:**\n\n"
                for i, crypto in enumerate(trending_data[:10], 1):
                    change_emoji = "📈" if crypto['change_24h'] >= 0 else "📉"
                    response += f"{i}. **{crypto['name']} ({crypto['symbol']})**\n"
                    response += f"   💵 ${crypto['price']:,.2f} {change_emoji} {crypto['change_24h']:+.2f}%\n\n"
                
                await query.edit_message_text(response, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ Could not fetch trending data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable.")
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in trending async: {str(e)}")
            await query.edit_message_text("❌ Error fetching trending data. Please try again.")

    async def _handle_funds_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Handle funds button press asynchronously."""
        try:
            # Show instant feedback
            await query.edit_message_text("⏳ Fetching funds data...")
            
            # Fetch data
            funds_data = await self.get_funds_data()
            
            if funds_data:
                response = "🏦 **Top Crypto Investment Funds:**\n\n"
                for i, fund in enumerate(funds_data[:10], 1):
                    response += f"{i}. **{fund['name']}**\n"
                    response += f"   🏢 Type: {fund['type']}\n"
                    response += f"   ⭐ Tier: {fund['tier']}\n\n"
                
                await query.edit_message_text(response, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ Could not fetch funds data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable.")
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in funds async: {str(e)}")
            await query.edit_message_text("❌ Error fetching funds data. Please try again.")

    async def _handle_drophunting_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query):
        """Handle drophunting button press asynchronously."""
        try:
            # Show instant feedback
            await query.edit_message_text("⏳ Fetching drophunting data...")
            
            # Fetch data
            drophunting_data = await self.get_drophunting_data()
            
            if drophunting_data:
                # Check if it's the cheeky error message
                if drophunting_data[0].get('error_message'):
                    response = f"🎯 **Drophunting Activities:**\n\n"
                    response += f"💸 **{drophunting_data[0]['name']}**\n"
                    response += f"   🎁 Reward: {drophunting_data[0]['reward_type']}\n"
                    response += f"   📊 Status: {drophunting_data[0]['status']}\n"
                    response += f"   📱 X Score: {drophunting_data[0]['x_score']}\n\n"
                    response += f"**{drophunting_data[0]['error_message']}**\n\n"
                    response += f"💡 *This endpoint requires a paid CryptoRank API subscription.*"
                else:
                    response = "🎯 **Drophunting Activities:**\n\n"
                    for i, activity in enumerate(drophunting_data[:10], 1):
                        response += f"{i}. **{activity['name']}**\n"
                        response += f"   🎁 Reward: {activity['reward_type']}\n"
                        response += f"   📊 Status: {activity['status']}\n"
                        if activity.get('total_raised'):
                            response += f"   💰 Raised: ${activity['total_raised']:,.0f}\n"
                        response += f"   📱 X Score: {activity.get('x_score', 'N/A')}\n\n"
                
                await query.edit_message_text(response, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ Could not fetch drophunting data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable.")
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in drophunting async: {str(e)}")
            await query.edit_message_text("❌ Error fetching drophunting data. Please try again.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle natural language messages."""
        try:
            if not update.message or not update.message.text:
                logger.error("[TELEGRAM] No message or text in update")
                return
                
            user_message = update.message.text.lower()
            
            # Crypto-related keywords
            crypto_keywords = [
                'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'cryptocurrency',
                'price', 'prices', 'market', 'trading', 'invest', 'investment',
                'trending', 'hot', 'pump', 'dump', 'bull', 'bear', 'moon',
                'drophunting', 'airdrop', 'rewards', 'funds', 'investors'
            ]
            
            # Check if message contains crypto keywords
            if any(keyword in user_message for keyword in crypto_keywords):
                await self.process_crypto_request(update, context)
            else:
                # Use AI model for general responses
                if self.model:
                    try:
                        ai_response = self.model.query(user_message)
                        await update.message.reply_text(ai_response)
                    except Exception as e:
                        logger.error(f"[TELEGRAM] AI model error: {str(e)}")
                        await update.message.reply_text(
                            "🤖 I'm DobbyXBT Bot, your crypto assistant! "
                            "Ask me about cryptocurrency prices, trending coins, or investment opportunities. "
                            "Use /help to see all commands."
                        )
                else:
                    await update.message.reply_text(
                        "🤖 I'm DobbyXBT Bot, your crypto assistant! "
                        "Ask me about cryptocurrency prices, trending coins, or investment opportunities. "
                        "Use /help to see all commands."
                    )
                    
        except Exception as e:
            logger.error(f"[TELEGRAM] Error handling message: {str(e)}")
            await update.message.reply_text("❌ Error processing message. Please try again.")

    async def process_crypto_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process crypto-related requests with AI assistance."""
        try:
            user_message = update.message.text.lower()
            
            # Use AI model for intelligent crypto analysis
            if self.model:
                try:
                    crypto_prompt = (
                        "You are DobbyXBT, a specialized cryptocurrency assistant. "
                        "Analyze the user's crypto request and provide helpful, accurate information. "
                        "Focus on: prices, market trends, investment opportunities, airdrops, and crypto funds. "
                        "Be concise and informative. If you need real data, mention that the user should use specific commands like /price, /trending, /funds, or /drophunting."
                    )
                    
                    ai_response = self.model.query(f"{crypto_prompt}\n\nUser: {user_message}")
                    await update.message.reply_text(ai_response)
                except Exception as e:
                    logger.error(f"[TELEGRAM] AI model error in crypto processing: {str(e)}")
                    # Fallback to basic response
                    await self.handle_basic_crypto_request(update, context)
            else:
                await self.handle_basic_crypto_request(update, context)
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error processing crypto request: {str(e)}")
            await update.message.reply_text("❌ Error processing crypto request. Please try again.")

    async def handle_basic_crypto_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle basic crypto requests without AI."""
        try:
            user_message = update.message.text.lower()
            
            if any(word in user_message for word in ['price', 'cost', 'value', 'worth']):
                await update.message.reply_text(
                    "💰 For crypto prices, use: /price <symbol>\n"
                    "Example: /price BTC"
                )
            elif any(word in user_message for word in ['trending', 'hot', 'popular', 'top']):
                await update.message.reply_text(
                    "📈 For trending cryptos, use: /trending"
                )
            elif any(word in user_message for word in ['fund', 'investor', 'investment']):
                await update.message.reply_text(
                    "🏦 For crypto funds, use: /funds"
                )
            elif any(word in user_message for word in ['drophunting', 'airdrop', 'reward']):
                await update.message.reply_text(
                    "🎯 For airdrop activities, use: /drophunting"
                )
            else:
                await update.message.reply_text(
                    "🤖 I'm DobbyXBT Bot! Use /help to see all available commands for crypto data."
                )
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in basic crypto request: {str(e)}")
            await update.message.reply_text("❌ Error processing request. Please try again.")

    def run(self):
        """Run the Telegram bot in polling mode (for local development)."""
        logger.info("[TELEGRAM] Starting DobbyXBT Bot...")
        
        # Initialize handlers
        self._initialize_handlers_only()
        
        # Start the bot with proper async handling
        logger.info("[TELEGRAM] Starting bot with improved connection handling...")
        
        try:
            # Use the standard run_polling method which handles async properly
            logger.info("[TELEGRAM] Starting polling...")
            logger.info("[TELEGRAM] Bot is now running! Press Ctrl+C to stop.")
            self.application.run_polling()
                
        except KeyboardInterrupt:
            logger.info("[TELEGRAM] Bot stopped by user.")
        except Exception as e:
            logger.error(f"[TELEGRAM] Bot error: {str(e)}")
            logger.info("[TELEGRAM] Please check your bot token and internet connection.")

    async def process_webhook_update(self, update_data: dict):
        """Process webhook update for Render deployment - SIMPLIFIED."""
        try:
            logger.info("[TELEGRAM] Starting webhook update processing...")
            
            # Ensure application is initialized
            if not self.application._initialized:
                logger.info("[TELEGRAM] Initializing application...")
                await self.application.initialize()
                logger.info("[TELEGRAM] Application initialized for webhook processing")
            
            # Create Update object from webhook data
            logger.info("[TELEGRAM] Creating Update object from webhook data...")
            update = Update.de_json(update_data, self.application.bot)
            
            if update:
                logger.info(f"[TELEGRAM] Update object created successfully: {update.update_id}")
                
                # Process the update
                logger.info("[TELEGRAM] Processing update...")
                await self.application.process_update(update)
                logger.info(f"[TELEGRAM] Successfully processed webhook update: {update.update_id}")
                return True
            else:
                logger.warning("[TELEGRAM] No update object created from webhook data")
                return False
            
        except Exception as e:
            logger.error(f"[TELEGRAM] Error processing webhook update: {str(e)}")
            import traceback
            logger.error(f"[TELEGRAM] Full traceback: {traceback.format_exc()}")
            return False
