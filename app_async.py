import os
import json
import logging
import asyncio
import aiohttp
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor

# Configure logging for Render - CLEAN VERSION
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Bot configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CRYPTO_API_KEY = os.getenv("CRYPTORANK_API_KEY")
CRYPTO_API_BASE_URL = "https://api.cryptorank.io/v2"

# Global session for async HTTP requests
http_session = None

async def get_http_session():
    """Get or create aiohttp session"""
    global http_session
    if http_session is None or http_session.closed:
        timeout = aiohttp.ClientTimeout(total=30)
        http_session = aiohttp.ClientSession(timeout=timeout)
    return http_session

async def send_telegram_message_async(chat_id, text, reply_markup=None):
    """Send message to Telegram using aiohttp (async)"""
    try:
        session = await get_http_session()
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        async with session.post(url, json=data) as response:
            result = await response.json()
            return result
    except Exception as e:
        logger.error(f"Error sending Telegram message: {str(e)}")
        return None

async def edit_telegram_message_async(chat_id, message_id, text, reply_markup=None):
    """Edit Telegram message using aiohttp (async)"""
    try:
        session = await get_http_session()
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        async with session.post(url, json=data) as response:
            result = await response.json()
            return result
    except Exception as e:
        logger.error(f"Error editing Telegram message: {str(e)}")
        return None

async def get_crypto_prices_async(symbol=None):
    """Get crypto prices from CryptoRank API (async)"""
    try:
        if not CRYPTO_API_KEY:
            return []
        
        session = await get_http_session()
        url = f"{CRYPTO_API_BASE_URL}/currencies"
        headers = {'X-Api-Key': CRYPTO_API_KEY}
        params = {
            'limit': 100,
            'sortBy': 'marketCap',
            'sortDirection': 'DESC'
        }
        if symbol:
            params['symbol'] = symbol.upper()
        
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data and 'data' in data:
                    prices = []
                    for currency in data.get('data', []):
                        try:
                            prices.append({
                                'symbol': currency.get('symbol', 'Unknown'),
                                'name': currency.get('name', 'Unknown'),
                                'price': float(currency.get('price', 0)) if currency.get('price') else 0,
                                'change_24h': float(currency.get('change24h', 0)) if currency.get('change24h') else 0,
                                'market_cap': float(currency.get('marketCap', 0)) if currency.get('marketCap') else 0,
                                'rank': currency.get('rank', 0)
                            })
                        except (ValueError, TypeError):
                            continue
                    # Return only first 20 results
                    return prices[:20]
            return []
    except Exception as e:
        logger.error(f"Error fetching crypto prices: {str(e)}")
        return []

async def get_trending_crypto_async():
    """Get trending crypto from CryptoRank API (async)"""
    try:
        if not CRYPTO_API_KEY:
            return []
        
        session = await get_http_session()
        url = f"{CRYPTO_API_BASE_URL}/currencies"
        headers = {'X-Api-Key': CRYPTO_API_KEY}
        params = {
            'limit': 100,
            'sortBy': 'marketCap',
            'sortDirection': 'DESC'
        }
        
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data and 'data' in data:
                    trending = []
                    for currency in data.get('data', []):
                        try:
                            trending.append({
                                'symbol': currency.get('symbol', 'Unknown'),
                                'name': currency.get('name', 'Unknown'),
                                'price': float(currency.get('price', 0)) if currency.get('price') else 0,
                                'change_24h': float(currency.get('change24h', 0)) if currency.get('change24h') else 0,
                                'market_cap': float(currency.get('marketCap', 0)) if currency.get('marketCap') else 0,
                                'rank': currency.get('rank', 0)
                            })
                        except (ValueError, TypeError):
                            continue
                        # Return only first 20 results
                        return trending[:20]
            return []
    except Exception as e:
        logger.error(f"Error fetching trending crypto: {str(e)}")
        return []

async def get_funds_data_async():
    """Get funds data from CryptoRank API (async)"""
    try:
        if not CRYPTO_API_KEY:
            return []
        
        session = await get_http_session()
        url = f"{CRYPTO_API_BASE_URL}/funds/map"
        headers = {'X-Api-Key': CRYPTO_API_KEY}
        params = {'limit': 20}
        
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data and 'data' in data:
                    funds = []
                    for fund in data.get('data', []):
                        try:
                            funds.append({
                                'name': fund.get('name', 'Unknown'),
                                'type': fund.get('type', 'Unknown'),
                                'tier': fund.get('tier', 'Unknown')
                            })
                        except (ValueError, TypeError):
                            continue
                    return funds
            return []
    except Exception as e:
        logger.error(f"Error fetching funds data: {str(e)}")
        return []

async def get_drophunting_data_async():
    """Get drophunting data from CryptoRank API (async)"""
    try:
        if not CRYPTO_API_KEY:
            return []
        
        session = await get_http_session()
        url = f"{CRYPTO_API_BASE_URL}/drophunting/activities"
        headers = {'X-Api-Key': CRYPTO_API_KEY}
        params = {'limit': 20}
        
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data and 'data' in data:
                    activities = []
                    for activity in data.get('data', []):
                        try:
                            activities.append({
                                'name': activity.get('name', 'Unknown'),
                                'reward_type': activity.get('reward_type', 'Unknown'),
                                'status': activity.get('status', 'Unknown'),
                                'x_score': activity.get('x_score', 'N/A'),
                                'total_raised': activity.get('total_raised', 0)
                            })
                        except (ValueError, TypeError):
                            continue
                    return activities
            elif response.status == 403:
                # Return cheeky error message for paid API
                return [{
                    'name': 'Drophunting Activities',
                    'reward_type': 'Premium Data',
                    'status': 'Paid API Required',
                    'x_score': 'N/A',
                    'error_message': '💰 The developer is too broke to afford the paid version of CryptoRank drophunting API endpoint! 😅'
                }]
            return []
    except Exception as e:
        logger.error(f"Error fetching drophunting data: {str(e)}")
        return []

def run_async_in_thread(coro):
    """Run async function in a separate thread with its own event loop"""
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_thread)
        return future.result(timeout=30)

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "Bot is running and ready for Telegram webhooks!",
        "message": "Visit /webhook to receive Telegram updates.",
        "commands": [
            "/price <symbol>",
            "/trending", 
            "/funds",
            "/drophunting"
        ],
        "natural_language_examples": [
            "What's the price of Bitcoin?",
            "Show me trending cryptocurrencies",
            "Top crypto investors and funds",
            "Show me airdrop activities"
        ]
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook updates - PROPER ASYNC APPROACH"""
    try:
        logger.info("Webhook request received")
        
        # Get update data
        update_data = request.get_json()
        
        if not update_data:
            return jsonify({'status': 'error', 'message': 'No update data'}), 400
        
        # Process the update asynchronously in a separate thread
        result = run_async_in_thread(process_telegram_update_async(update_data))
        
        if result:
            return jsonify({'status': 'ok'})
        else:
            return jsonify({'status': 'error', 'message': 'Processing failed'}), 400
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Webhook error: {str(e)}'}), 500

async def process_telegram_update_async(update_data):
    """Process Telegram update asynchronously"""
    try:
        # Handle different types of updates
        if 'message' in update_data:
            return await handle_message_async(update_data)
        elif 'callback_query' in update_data:
            return await handle_callback_query_async(update_data)
        else:
            logger.warning(f"Unknown update type: {update_data}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing Telegram update: {str(e)}")
        return False

async def handle_message_async(update_data):
    """Handle text messages asynchronously"""
    try:
        message = update_data['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        # Process message
        
        if text.startswith('/start'):
            # Send welcome message with buttons
            welcome_text = (
                "🤖 Welcome to DobbyXBT Bot!\n\n"
                "I'm your AI-powered cryptocurrency assistant! 🚀\n\n"
                "What I can do:\n"
                "💰 Get real-time crypto prices\n"
                "📈 Show trending cryptocurrencies\n"
                "🏦 Find top crypto investors & funds\n"
                "🎯 Discover airdrop opportunities\n"
                "💬 Chat naturally about crypto\n\n"
                "Created by [pipsandbills](https://x.com/pipsandbills)\n\n"
                "Use /help to see all commands!"
            )
            
            keyboard = {
                'inline_keyboard': [
                    [{'text': '💰 Price', 'callback_data': 'price_menu'}],
                    [{'text': '📈 Trending', 'callback_data': 'trending_menu'}],
                    [{'text': '🏦 Funds', 'callback_data': 'funds_menu'}],
                    [{'text': '🎯 Drophunting', 'callback_data': 'drophunting_menu'}]
                ]
            }
            
            await send_telegram_message_async(chat_id, welcome_text, keyboard)
            return True
            
        elif text.startswith('/help'):
            help_text = (
                "🤖 **DobbyXBT Bot Commands:**\n\n"
                "💰 `/price <symbol>` - Get crypto price\n"
                "📈 `/trending` - Top trending cryptos\n"
                "🏦 `/funds` - Top crypto investment funds\n"
                "🎯 `/drophunting` - Airdrop opportunities\n\n"
                "💬 **Natural Language:**\n"
                "Ask me anything about crypto!"
            )
            await send_telegram_message_async(chat_id, help_text)
            return True
            
        elif text.startswith('/price'):
            # Handle price command
            parts = text.split()
            symbol = parts[1] if len(parts) > 1 else None
            
            if symbol:
                # Show loading message first
                loading_msg = await send_telegram_message_async(chat_id, f"⏳ Fetching price data for {symbol.upper()}...")
                
                prices = await get_crypto_prices_async(symbol)
                if prices:
                    price = prices[0]
                    response = (
                        f"💰 **{price['name']} ({price['symbol']})**\n\n"
                        f"💵 Price: ${price['price']:,.2f}\n"
                        f"📊 24h Change: {price['change_24h']:+.2f}%\n"
                        f"🏆 Market Cap: ${price['market_cap']:,.0f}\n"
                        f"📈 Rank: #{price['rank']}"
                    )
                else:
                    response = f"❌ Could not find data for {symbol.upper()}. Please check the symbol and try again.\n\nTry: BTC, ETH, ADA, SOL, etc."
                
                # Edit the loading message with the result
                if loading_msg and 'result' in loading_msg:
                    message_id = loading_msg['result']['message_id']
                    await edit_telegram_message_async(chat_id, message_id, response)
                else:
                    await send_telegram_message_async(chat_id, response)
            else:
                response = "❌ Please provide a cryptocurrency symbol. Example: /price BTC"
                await send_telegram_message_async(chat_id, response)
            
            return True
            
        elif text.startswith('/trending'):
            # Handle trending command
            trending_data = await get_trending_crypto_async()
            if trending_data:
                response = "🔥 **Top Trending Cryptocurrencies:**\n\n"
                for i, crypto in enumerate(trending_data[:10], 1):
                    change_emoji = "📈" if crypto['change_24h'] >= 0 else "📉"
                    response += f"{i}. **{crypto['name']} ({crypto['symbol']})**\n"
                    response += f"   💵 ${crypto['price']:,.2f} {change_emoji} {crypto['change_24h']:+.2f}%\n\n"
            else:
                response = "❌ Could not fetch trending data. Please set your CryptoRank API key."
            
            await send_telegram_message_async(chat_id, response)
            return True
            
        elif text.startswith('/funds'):
            # Handle funds command
            funds_data = await get_funds_data_async()
            if funds_data:
                response = "🏦 **Top Crypto Investment Funds:**\n\n"
                for i, fund in enumerate(funds_data[:10], 1):
                    response += f"{i}. **{fund['name']}**\n"
                    response += f"   🏢 Type: {fund['type']}\n"
                    response += f"   ⭐ Tier: {fund['tier']}\n\n"
            else:
                response = "❌ Could not fetch funds data. Please set your CryptoRank API key."
            
            await send_telegram_message_async(chat_id, response)
            return True
            
        elif text.startswith('/drophunting'):
            # Handle drophunting command
            drophunting_data = await get_drophunting_data_async()
            if drophunting_data:
                if drophunting_data[0].get('error_message'):
                    response = (
                        f"🎯 **Drophunting Activities:**\n\n"
                        f"💸 **{drophunting_data[0]['name']}**\n"
                        f"   🎁 Reward: {drophunting_data[0]['reward_type']}\n"
                        f"   📊 Status: {drophunting_data[0]['status']}\n"
                        f"   📱 X Score: {drophunting_data[0]['x_score']}\n\n"
                        f"**{drophunting_data[0]['error_message']}**\n\n"
                        f"💡 *This endpoint requires a paid CryptoRank API subscription.*"
                    )
                else:
                    response = "🎯 **Drophunting Activities:**\n\n"
                    for i, activity in enumerate(drophunting_data[:10], 1):
                        response += f"{i}. **{activity['name']}**\n"
                        response += f"   🎁 Reward: {activity['reward_type']}\n"
                        response += f"   📊 Status: {activity['status']}\n"
                        if activity.get('total_raised'):
                            response += f"   💰 Raised: ${activity['total_raised']:,.0f}\n"
                        response += f"   📱 X Score: {activity.get('x_score', 'N/A')}\n\n"
            else:
                response = "❌ Could not fetch drophunting data. Please set your CryptoRank API key."
            
            await send_telegram_message_async(chat_id, response)
            return True
            
        else:
            # Handle natural language
            response = (
                "💬 I understand you're asking about crypto!\n\n"
                "Try these commands:\n"
                "💰 `/price BTC` - Get Bitcoin price\n"
                "📈 `/trending` - Top trending cryptos\n"
                "🏦 `/funds` - Top crypto funds\n"
                "🎯 `/drophunting` - Airdrop opportunities\n\n"
                "Or use the buttons below! 👇"
            )
            await send_telegram_message_async(chat_id, response)
            return True
            
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        return False

async def handle_callback_query_async(update_data):
    """Handle button callbacks asynchronously"""
    try:
        callback_query = update_data['callback_query']
        chat_id = callback_query['message']['chat']['id']
        message_id = callback_query['message']['message_id']
        data = callback_query['data']
        
        # Process callback
        
        # Answer the callback query
        session = await get_http_session()
        answer_url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
        async with session.post(answer_url, json={'callback_query_id': callback_query['id']}) as response:
            await response.json()
        
        if data == "price_menu":
            response = (
                "💰 **Price Lookup**\n\n"
                "Use /price <symbol> to get real-time prices.\n"
                "Example: /price BTC\n\n"
                "Supported symbols: BTC, ETH, ADA, SOL, etc."
            )
            await edit_telegram_message_async(chat_id, message_id, response)
            return True
            
        elif data == "trending_menu":
            # Show loading message first
            await edit_telegram_message_async(chat_id, message_id, "⏳ Fetching trending data...")
            
            # Get trending data
            trending_data = await get_trending_crypto_async()
            if trending_data:
                response = "🔥 **Top Trending Cryptocurrencies:**\n\n"
                for i, crypto in enumerate(trending_data[:10], 1):
                    change_emoji = "📈" if crypto['change_24h'] >= 0 else "📉"
                    response += f"{i}. **{crypto['name']} ({crypto['symbol']})**\n"
                    response += f"   💵 ${crypto['price']:,.2f} {change_emoji} {crypto['change_24h']:+.2f}%\n\n"
            else:
                response = "❌ Could not fetch trending data. Please set your CryptoRank API key."
            
            await edit_telegram_message_async(chat_id, message_id, response)
            return True
            
        elif data == "funds_menu":
            # Show loading message first
            await edit_telegram_message_async(chat_id, message_id, "⏳ Fetching funds data...")
            
            # Get funds data
            funds_data = await get_funds_data_async()
            if funds_data:
                response = "🏦 **Top Crypto Investment Funds:**\n\n"
                for i, fund in enumerate(funds_data[:10], 1):
                    response += f"{i}. **{fund['name']}**\n"
                    response += f"   🏢 Type: {fund['type']}\n"
                    response += f"   ⭐ Tier: {fund['tier']}\n\n"
            else:
                response = "❌ Could not fetch funds data. Please set your CryptoRank API key."
            
            await edit_telegram_message_async(chat_id, message_id, response)
            return True
            
        elif data == "drophunting_menu":
            # Show loading message first
            await edit_telegram_message_async(chat_id, message_id, "⏳ Fetching drophunting data...")
            
            # Get drophunting data
            drophunting_data = await get_drophunting_data_async()
            if drophunting_data:
                if drophunting_data[0].get('error_message'):
                    response = (
                        f"🎯 **Drophunting Activities:**\n\n"
                        f"💸 **{drophunting_data[0]['name']}**\n"
                        f"   🎁 Reward: {drophunting_data[0]['reward_type']}\n"
                        f"   📊 Status: {drophunting_data[0]['status']}\n"
                        f"   📱 X Score: {drophunting_data[0]['x_score']}\n\n"
                        f"**{drophunting_data[0]['error_message']}**\n\n"
                        f"💡 *This endpoint requires a paid CryptoRank API subscription.*"
                    )
                else:
                    response = "🎯 **Drophunting Activities:**\n\n"
                    for i, activity in enumerate(drophunting_data[:10], 1):
                        response += f"{i}. **{activity['name']}**\n"
                        response += f"   🎁 Reward: {activity['reward_type']}\n"
                        response += f"   📊 Status: {activity['status']}\n"
                        if activity.get('total_raised'):
                            response += f"   💰 Raised: ${activity['total_raised']:,.0f}\n"
                        response += f"   📱 X Score: {activity.get('x_score', 'N/A')}\n\n"
            else:
                response = "❌ Could not fetch drophunting data. Please set your CryptoRank API key."
            
            await edit_telegram_message_async(chat_id, message_id, response)
            return True
            
        return True
        
    except Exception as e:
        logger.error(f"Error handling callback query: {str(e)}")
        return False

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Set Telegram webhook URL"""
    try:
        import requests
        
        if not BOT_TOKEN:
            return jsonify({'error': 'TELEGRAM_BOT_TOKEN not set'}), 500
        
        # Get the webhook URL from Render environment
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        if not render_url:
            return jsonify({'error': 'RENDER_EXTERNAL_URL not set'}), 500
        
        webhook_url = f"{render_url}/webhook"
        # Setting webhook
        
        # Set webhook via Telegram API
        telegram_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        response = requests.post(telegram_api_url, json={'url': webhook_url})
        
        # Set webhook response
        
        if response.status_code == 200 and response.json().get('ok'):
            return jsonify({
                'status': 'success',
                'message': f'Webhook set to {webhook_url}',
                'telegram_response': response.json()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to set webhook',
                'telegram_response': response.json()
            }), 400
            
    except Exception as e:
        logger.error(f"Error setting webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook_info', methods=['GET'])
def webhook_info():
    """Get current webhook information"""
    try:
        import requests
        
        if not BOT_TOKEN:
            return jsonify({'error': 'TELEGRAM_BOT_TOKEN not set'}), 500
        
        # Get webhook info via Telegram API
        telegram_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        response = requests.get(telegram_api_url)
        
        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'webhook_info': response.json()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get webhook info',
                'telegram_response': response.json()
            }), 400
            
    except Exception as e:
        logger.error(f"Error getting webhook info: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # For local development
    logger.info("Starting Flask app for DobbyXBT Bot...")
    logger.info("Bot is ready to receive webhook requests!")
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
