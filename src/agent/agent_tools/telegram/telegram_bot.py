import logging
import asyncio
import aiohttp  
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes 
from src.agent.agent_tools.telegram.telegram_config import TelegramConfig

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig(format="%(levelname)s: %(message)s")

class Telegram:
    def __init__(self, token, model=None):
        logger.info("[TELEGRAM] Initializing DobbyXBT Bot...")
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
        else:
            logger.warning("[TELEGRAM] API key cleared.")


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

    def run(self):
        """Run the Telegram bot."""
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

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command."""
        keyboard = [
            [InlineKeyboardButton("💰 Price Check", callback_data="price_menu")],
            [InlineKeyboardButton("🔥 Trending", callback_data="trending_menu")],
            [InlineKeyboardButton("🏦 Funds", callback_data="funds_menu")],
            [InlineKeyboardButton("🎯 Drophunting", callback_data="drophunting_menu")],
            [InlineKeyboardButton("❓ Help", callback_data="help_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = (
            f"🚀 **Welcome to DobbyXBT Bot!**\n\n"
            f"I'm your AI-powered cryptocurrency assistant. I can help you with:\n\n"
            f"💰 **Price Tracking** - Get real-time crypto prices\n"
            f"🔥 **Trending Assets** - Hot cryptocurrencies\n"
            f"🏦 **Investment Data** - Top crypto investors and funds\n"
            f"🎯 **Drophunting** - Airdrop activities and rewards\n\n"
            f"Use the buttons below or type your request naturally!\n\n"
            f"Created by [pipsandbills](https://x.com/pipsandbills)"
        )
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command."""
        help_message = (
            f"🆘 **DobbyXBT Bot Commands:**\n\n"
            f"**📋 Main Commands:**\n"
            f"/start - Welcome message and main menu\n"
            f"/help - Show this help message\n\n"
            f"**💰 Price Commands:**\n"
            f"/price <symbol> - Get current price (e.g., /price BTC)\n"
            f"/price <symbol1,symbol2> - Compare prices\n\n"
            f"**🔥 Market Commands:**\n"
            f"/trending - Trending cryptocurrencies\n"
            f"/trending gainers - Top gainers\n"
            f"/trending losers - Top losers\n\n"
            f"**🏦 Investment Commands:**\n"
            f"/funds - Top crypto investors and funds\n\n"
            f"**🎯 Drophunting Commands:**\n"
            f"/drophunting - Airdrop activities\n"
            f"/drophunting POTENTIAL - Activities with potential status\n\n"
            f"**💬 Natural Language:**\n"
            f"Just type naturally! Examples:\n"
            f"• 'What's the price of Bitcoin?'\n"
            f"• 'Show me trending cryptocurrencies'\n"
            f"• 'Top crypto investors and funds'\n"
            f"• 'Show me airdrop activities'"
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')

    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command for cryptocurrency prices."""
        try:
            args = context.args
            if not args:
                await update.message.reply_text(
                    "💰 **Price Check**\n\n"
                    "Usage: `/price BTC` or `/price BTC,ETH`\n"
                    "Example: `/price bitcoin`",
                    parse_mode='Markdown'
                )
                return
            
            symbols = [arg.upper() for arg in args[0].split(',')]
            prices = await self.get_crypto_prices(symbols)
            
            if prices:
                response = "💰 **Current Prices:**\n\n"
                for price_data in prices:
                    # Safely convert price to float
                    try:
                        price = float(price_data['price']) if price_data['price'] else 0
                        response += f"**{price_data['symbol']}**: ${price:,.2f}\n"
                    except (ValueError, TypeError):
                        response += f"**{price_data['symbol']}**: ${price_data['price']}\n"
                    
                    # Safely handle change_24h
                    if price_data.get('change_24h'):
                        try:
                            change = float(price_data['change_24h'])
                            change_emoji = "📈" if change > 0 else "📉"
                            response += f"{change_emoji} 24h: {change:+.2f}%\n"
                        except (ValueError, TypeError):
                            response += f"📊 24h: {price_data['change_24h']}\n"
                    
                    # Safely handle market cap
                    market_cap = price_data.get('market_cap', 'N/A')
                    if market_cap != 'N/A':
                        try:
                            market_cap = float(market_cap)
                            response += f"Market Cap: ${market_cap:,.0f}\n\n"
                        except (ValueError, TypeError):
                            response += f"Market Cap: ${market_cap}\n\n"
                    else:
                        response += f"Market Cap: {market_cap}\n\n"
                
                await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Could not fetch price data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable.")
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in price command: {str(e)}")
            await update.message.reply_text("❌ Error fetching price data. Please try again.")




    async def trending_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trending command for trending cryptocurrencies."""
        try:
            args = context.args
            trend_type = args[0] if args else "trending"
            
            trending_data = await self.get_trending_crypto(trend_type)
            if trending_data:
                response = f"🔥 **{trend_type.title()} Cryptocurrencies:**\n\n"
                
                for i, crypto in enumerate(trending_data[:10], 1):
                    # Safely convert price to float
                    try:
                        price = float(crypto['price']) if crypto['price'] else 0
                        response += f"{i}. **{crypto['symbol']}** - ${price:,.2f}\n"
                    except (ValueError, TypeError):
                        response += f"{i}. **{crypto['symbol']}** - ${crypto['price']}\n"
                    
                    # Safely handle change_24h
                    try:
                        change = float(crypto['change_24h']) if crypto['change_24h'] else 0
                        change_emoji = "📈" if change > 0 else "📉"
                        response += f"   {change_emoji} {change:+.2f}% (24h)\n"
                    except (ValueError, TypeError):
                        response += f"   📊 {crypto['change_24h']} (24h)\n"
                    
                    # Safely handle market cap
                    market_cap = crypto.get('market_cap', 'N/A')
                    if market_cap != 'N/A':
                        try:
                            market_cap = float(market_cap)
                            response += f"   Market Cap: ${market_cap:,.0f}\n\n"
                        except (ValueError, TypeError):
                            response += f"   Market Cap: ${market_cap}\n\n"
                    else:
                        response += f"   Market Cap: {market_cap}\n\n"
                
                await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Could not fetch trending data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable.")
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in trending command: {str(e)}")
            await update.message.reply_text("❌ Error fetching trending data. Please try again.")

    async def funds_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /funds command for investor and fund data."""
        try:
            funds_data = await self.get_funds_data()
            if funds_data:
                response = "🏦 **Top Crypto Investors & Funds:**\n\n"
                
                for i, fund in enumerate(funds_data[:10], 1):
                    tier_emoji = "🥇" if fund['tier'] == 1 else "🥈" if fund['tier'] == 2 else "🥉"
                    response += f"{i}. **{fund['name']}**\n"
                    response += f"   {tier_emoji} Type: {fund['type']}\n"
                    response += f"   Tier: {fund['tier']}\n\n"
                
                await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Could not fetch funds data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable.")
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in funds command: {str(e)}")
            await update.message.reply_text("❌ Error fetching funds data. Please try again.")

    async def drophunting_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /drophunting command for airdrop activities."""
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
                
                await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Could not fetch drophunting data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable.")
                
        except Exception as e:
            logger.error(f"[TELEGRAM] Error in drophunting command: {str(e)}")
            await update.message.reply_text("❌ Error fetching drophunting data. Please try again.")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "price_menu":
            await query.edit_message_text(
                "💰 **Price Check**\n\n"
                "Type: `/price BTC` or `/price BTC,ETH`\n"
                "Or ask naturally: 'What's the price of Bitcoin?'",
                parse_mode='Markdown'
            )
        elif query.data == "trending_menu":
            await query.edit_message_text(
                "🔥 **Trending Cryptocurrencies**\n\n"
                "`/trending` - Trending coins\n"
                "`/trending gainers` - Top gainers\n"
                "`/trending losers` - Top losers",
                parse_mode='Markdown'
            )
        elif query.data == "funds_menu":
            await query.edit_message_text(
                "🏦 **Crypto Investors & Funds**\n\n"
                "`/funds` - Top crypto investors and funds\n"
                "Shows tier-1 investors, VCs, and hedge funds",
                parse_mode='Markdown'
            )
        elif query.data == "drophunting_menu":
            await query.edit_message_text(
                "🎯 **Drophunting Activities**\n\n"
                "`/drophunting` - All airdrop activities\n"
                "`/drophunting POTENTIAL` - Potential airdrops\n"
                "`/drophunting CONFIRMED` - Confirmed airdrops\n"
                "Shows airdrop activities, rewards, and status",
                parse_mode='Markdown'
            )
        elif query.data == "help_menu":
            await self.help_command(update, context)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages with crypto-specific natural language processing."""
        user_message = update.message.text
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logger.info(f"[TELEGRAM] Message from {username} (ID: {user_id}): {user_message}")
        
        try:
            # Use AI model for intelligent processing
            if self.model:
                # Create a comprehensive prompt for the AI model
                ai_prompt = f"""
You are DobbyXBT, an advanced cryptocurrency assistant bot with access to real-time crypto data via CryptoRank API. 

User message: "{user_message}"

You can:
- Get real-time crypto prices and market data
- Analyze market trends and provide insights
- Answer questions about blockchain technology and crypto concepts
- Provide market analysis and investment insights
- Share trending cryptocurrencies and market data
- Explain complex crypto concepts in simple terms

Available commands:
- /price <symbol> - Get current price
- /trending - Trending cryptocurrencies
- /funds - Top crypto investors and funds
- /drophunting - Airdrop activities

Respond intelligently and helpfully. If the user asks for specific data (prices, trending, etc.), acknowledge that you can fetch real data and provide helpful context. Use emojis appropriately and keep responses engaging but concise.

If the message is not crypto-related, politely redirect to crypto topics while being helpful.
"""
                response = self.model.query(ai_prompt)
            else:
                # Fallback to basic crypto keyword detection
                crypto_keywords = ['price', 'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'trending', 'market', 'funds', 'investors', 'vc', 'hedge', 'drophunting', 'airdrop', 'rewards']
                is_crypto_request = any(keyword in user_message.lower() for keyword in crypto_keywords)
                
                if is_crypto_request:
                    response = await self.process_crypto_request(user_message)
                else:
                    response = (
                        f"🚀 **DobbyXBT Bot**\n\n"
                        f"I'm your cryptocurrency assistant! I can help you with:\n\n"
                        f"💰 **Prices** - `/price BTC` or ask 'What's Bitcoin's price?'\n"
                        f"🔥 **Trending** - `/trending` for hot cryptocurrencies\n"
                        f"🏦 **Funds** - `/funds` for top crypto investors\n"
                        f"🎯 **Drophunting** - `/drophunting` for airdrop activities\n\n"
                        f"Type /help for all commands!"
                    )
            
            # Send response
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"[TELEGRAM] Response sent to {username}")
            
        except Exception as e:
            logger.error(f"[TELEGRAM] Error processing message from {username}: {str(e)}")
            error_message = (
                f"❌ Sorry, I encountered an error processing your request. "
                f"Please try again or use one of the available commands."
            )
            await update.message.reply_text(error_message)

    async def process_crypto_request(self, message: str) -> str:
        """Process crypto-specific natural language requests with AI intelligence."""
        message_lower = message.lower()
        
        # Use AI model for intelligent crypto analysis
        if self.model:
            ai_crypto_prompt = f"""
You are an expert cryptocurrency analyst with access to real-time market data. 

User message: "{message}"

Analyze this crypto request intelligently and provide:
- Market insights and analysis
- Price predictions and trends
- Risk assessments
- Investment advice
- Technical analysis
- Market sentiment

If the user asks for specific data (prices, trending, etc.), acknowledge that you can fetch real data and provide context. Be helpful, accurate, and use appropriate emojis.

Keep responses engaging but concise. Focus on being educational and informative.
"""
            return self.model.query(ai_crypto_prompt)
        
        # Price requests - ACTUALLY PROCESS THEM
        if any(word in message_lower for word in ['price', 'cost', 'value', 'worth', 'how much']):
            # Extract potential symbols
            symbols = []
            for word in message.split():
                if word.upper() in ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'MATIC', 'AVAX', 'LINK', 'UNI', 'AAVE', 'BITCOIN', 'ETHEREUM']:
                    symbols.append(word.upper())
            
            # If no symbols found, try to extract from common phrases
            if not symbols:
                if 'bitcoin' in message_lower or 'btc' in message_lower:
                    symbols.append('BTC')
                elif 'ethereum' in message_lower or 'eth' in message_lower:
                    symbols.append('ETH')
                elif 'solana' in message_lower or 'sol' in message_lower:
                    symbols.append('SOL')
                elif 'cardano' in message_lower or 'ada' in message_lower:
                    symbols.append('ADA')
                else:
                    # Default to BTC if no specific coin mentioned
                    symbols.append('BTC')
            
            if symbols:
                prices = await self.get_crypto_prices(symbols)
                if prices:
                    response = "💰 **Current Prices:**\n\n"
                    for price_data in prices:
                        # Safely convert price to float
                        try:
                            price = float(price_data['price']) if price_data['price'] else 0
                            response += f"**{price_data['symbol']}**: ${price:,.2f}\n"
                        except (ValueError, TypeError):
                            response += f"**{price_data['symbol']}**: ${price_data['price']}\n"
                        
                        # Safely handle change_24h
                        if price_data.get('change_24h'):
                            try:
                                change = float(price_data['change_24h'])
                                change_emoji = "📈" if change > 0 else "📉"
                                response += f"{change_emoji} 24h: {change:+.2f}%\n"
                            except (ValueError, TypeError):
                                response += f"📊 24h: {price_data['change_24h']}\n"
                        
                        # Safely handle market cap
                        market_cap = price_data.get('market_cap', 'N/A')
                        if market_cap != 'N/A':
                            try:
                                market_cap = float(market_cap)
                                response += f"Market Cap: ${market_cap:,.0f}\n\n"
                            except (ValueError, TypeError):
                                response += f"Market Cap: ${market_cap}\n\n"
                        else:
                            response += f"Market Cap: {market_cap}\n\n"
                    return response
                else:
                    return "❌ Could not fetch price data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable."
            else:
                return "💰 **Price Check**\n\nTry: `/price BTC` or ask 'What's Bitcoin's price?'"
        
        
        # Trending requests - ACTUALLY PROCESS THEM
        elif any(word in message_lower for word in ['trending', 'hot', 'popular', 'gaining', 'losing']):
            trending_data = await self.get_trending_crypto()
            if trending_data:
                response = "🔥 **Trending Cryptocurrencies:**\n\n"
                for i, crypto in enumerate(trending_data[:5], 1):
                    # Safely convert price to float
                    try:
                        price = float(crypto['price']) if crypto['price'] else 0
                        response += f"{i}. **{crypto['symbol']}** - ${price:,.2f}\n"
                    except (ValueError, TypeError):
                        response += f"{i}. **{crypto['symbol']}** - ${crypto['price']}\n"
                    
                    # Safely handle change_24h
                    try:
                        change = float(crypto['change_24h']) if crypto['change_24h'] else 0
                        change_emoji = "📈" if change > 0 else "📉"
                        response += f"   {change_emoji} {change:+.2f}% (24h)\n\n"
                    except (ValueError, TypeError):
                        response += f"   📊 {crypto['change_24h']} (24h)\n\n"
                return response
            else:
                return "❌ Could not fetch trending data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable."
        
        # Funds requests - ACTUALLY PROCESS THEM
        elif any(word in message_lower for word in ['funds', 'investors', 'vc', 'hedge', 'capital', 'investment']):
            funds_data = await self.get_funds_data()
            if funds_data:
                response = "🏦 **Top Crypto Investors & Funds:**\n\n"
                for i, fund in enumerate(funds_data[:5], 1):
                    tier_emoji = "🥇" if fund['tier'] == 1 else "🥈" if fund['tier'] == 2 else "🥉"
                    response += f"{i}. **{fund['name']}**\n"
                    response += f"   {tier_emoji} Type: {fund['type']}\n\n"
                return response
            else:
                return "❌ Could not fetch funds data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable."
        
        # Drophunting requests - ACTUALLY PROCESS THEM
        elif any(word in message_lower for word in ['drophunting', 'airdrop', 'rewards', 'activities', 'drops']):
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
                    for i, activity in enumerate(drophunting_data[:5], 1):
                        response += f"{i}. **{activity['name']}**\n"
                        response += f"   🎁 Reward: {activity['reward_type']}\n"
                        response += f"   📊 Status: {activity['status']}\n"
                        if activity.get('total_raised'):
                            response += f"   💰 Raised: ${activity['total_raised']:,.0f}\n"
                        response += f"   📱 X Score: {activity.get('x_score', 'N/A')}\n\n"
                return response
            else:
                return "❌ Could not fetch drophunting data. Please set your CryptoRank API key using the CRYPTORANK_API_KEY environment variable."
        
        # General crypto help
        else:
            return (
                f"🚀 **DobbyXBT Bot**\n\n"
                f"I can help you with cryptocurrency information! Try:\n\n"
                f"💰 **Prices**: 'What's Bitcoin's price?' or `/price BTC`\n"
                f"🔥 **Trending**: 'Trending cryptos' or `/trending`\n"
                f"🏦 **Funds**: 'Top crypto investors' or `/funds`\n"
                f"🎯 **Drophunting**: 'Show me airdrop activities' or `/drophunting`\n\n"
                f"Type /help for all commands!"
            )

    # CryptoRank API Integration Methods
    async def get_crypto_prices(self, symbols: list) -> list:
        """Get cryptocurrency prices from CryptoRank v2 API."""
        try:
            if not self.cryptorank_api_key:
                logger.error("[TELEGRAM] No CryptoRank API key provided. Please set CRYPTORANK_API_KEY environment variable or use set_api_key() method.")
                return []
            
            async with aiohttp.ClientSession() as session:
                # Use v2 /currencies endpoint with symbol filter
                symbol_str = ','.join(symbols)
                url = f"{self.cryptorank_base_url}/currencies"
                params = {
                    'symbol': symbol_str,
                    'limit': 100,
                    'sortBy': 'rank',
                    'sortDirection': 'ASC',
                    'include': 'percentChange'
                }
                headers = {
                    'X-Api-Key': self.cryptorank_api_key
                }
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        prices = []
                        for currency in data.get('data', []):
                            prices.append({
                                'symbol': currency['symbol'],
                                'price': currency.get('price', 0),
                                'change_24h': currency.get('percentChange', {}).get('24h', 0),
                                'market_cap': currency.get('marketCap', 0)
                            })
                        return prices
                    else:
                        logger.error(f"[TELEGRAM] CryptoRank API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"[TELEGRAM] Error fetching crypto prices: {str(e)}")
            return []




    async def get_trending_crypto(self, trend_type: str = "trending") -> list:
        """Get trending cryptocurrencies from CryptoRank v2 API."""
        try:
            if not self.cryptorank_api_key:
                logger.error("[TELEGRAM] No CryptoRank API key provided. Please set CRYPTORANK_API_KEY environment variable or use set_api_key() method.")
                return []
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.cryptorank_base_url}/currencies"
                
                # Determine sorting based on trend type
                if trend_type == "gainers":
                    sort_by = "percentChange"
                    sort_direction = "DESC"
                elif trend_type == "losers":
                    sort_by = "percentChange"
                    sort_direction = "ASC"
                else:  # trending
                    sort_by = "marketCap"
                    sort_direction = "DESC"
                
                params = {
                    'limit': 100,
                    'sortBy': sort_by,
                    'sortDirection': sort_direction,
                    'include': 'percentChange'
                }
                headers = {
                    'X-Api-Key': self.cryptorank_api_key
                }
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        trending = []
                        for currency in data.get('data', [])[:10]:
                            trending.append({
                                'symbol': currency['symbol'],
                                'price': currency.get('price', 0),
                                'change_24h': currency.get('percentChange', {}).get('24h', 0),
                                'market_cap': currency.get('marketCap', 0)
                            })
                        return trending
                    else:
                        logger.error(f"[TELEGRAM] CryptoRank trending API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"[TELEGRAM] Error fetching trending crypto: {str(e)}")
            return []

    async def get_funds_data(self) -> list:
        """Get investor and fund data from CryptoRank v2 API."""
        try:
            if not self.cryptorank_api_key:
                logger.error("[TELEGRAM] No CryptoRank API key provided. Please set CRYPTORANK_API_KEY environment variable or use set_api_key() method.")
                return []
            
            async with aiohttp.ClientSession() as session:
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
                                'tier': fund.get('tier', 0)
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
            
            async with aiohttp.ClientSession() as session:
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
                            'name': 'Developer Too Broke',
                            'reward_type': 'Paid API Required',
                            'status': '403 Forbidden',
                            'total_raised': 0,
                            'x_score': '💸',
                            'subscriber_count': 0,
                            'error_message': 'The developer is too broke to afford the paid version of CryptoRank drophunting API endpoint! '
                        }]
                    else:
                        logger.error(f"[TELEGRAM] CryptoRank drophunting API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"[TELEGRAM] Error fetching drophunting data: {str(e)}")
            return []


    async def send_message_to_user(self, user_id: int, message: str):
        """Send a message to a specific user (for API-triggered responses)."""
        try:
            await self.application.bot.send_message(chat_id=user_id, text=message)
            logger.info(f"[TELEGRAM] Message sent to user {user_id}")
        except Exception as e:
            logger.error(f"[TELEGRAM] Failed to send message to user {user_id}: {str(e)}")

    def stop(self):
        """Stop the bot."""
        if self.application:
            logger.info("[TELEGRAM] Stopping Telegram bot...")
            # Note: In a real implementation, you'd want to properly shutdown the application
            pass
