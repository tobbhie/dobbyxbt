"""
Vercel API endpoint for bot information and setup
Access via: https://your-app.vercel.app/api/index
"""
import json
import os
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    """Main information endpoint"""
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Get the current domain from headers
            host = self.headers.get('Host', 'dobbyxbt.vercel.app')
            
            # Check if bot token is configured
            bot_configured = bool(os.getenv("TELEGRAM_BOT_TOKEN"))
            api_configured = bool(os.getenv("CRYPTORANK_API_KEY"))
            
            response_data = {
                "bot_name": "CryptoRank Telegram Bot",
                "status": "deployed" if bot_configured else "needs_configuration",
                "version": "1.0.0",
                "features": [
                    "💰 Real-time cryptocurrency prices",
                    "🔥 Trending cryptocurrencies",
                    "🏦 Investment funds data",
                    "🎯 Drophunting activities (airdrop tracking)",
                    "🤖 AI-powered natural language processing"
                ],
                "configuration": {
                    "telegram_bot_token": "✅ Configured" if bot_configured else "❌ Not configured",
                    "cryptorank_api_key": "✅ Configured" if api_configured else "❌ Not configured",
                    "ai_model": "✅ Configured" if os.getenv("MODEL_API_KEY") else "⚠️ Optional - Not configured"
                },
                "endpoints": {
                    "webhook": f"https://{host}/api/webhook",
                    "setup": f"https://{host}/api/setup",
                    "health": f"https://{host}/api/index"
                },
                "setup_instructions": [
                    "1. Configure environment variables in Vercel dashboard",
                    f"2. Visit https://{host}/api/setup?action=set to configure webhook",
                    "3. Test your bot by sending /start on Telegram",
                    f"4. Use https://{host}/api/setup?action=info to check status"
                ],
                "commands": [
                    "/start - Welcome message and main menu",
                    "/help - Show all available commands",
                    "/price BTC - Get Bitcoin price",
                    "/trending - Show trending cryptocurrencies",
                    "/funds - Show top crypto investors",
                    "/drophunting - Show airdrop activities"
                ]
            }
            
            self._send_response(200, response_data)
            
        except Exception as e:
            self._send_error(500, f"Error: {str(e)}")
    
    def _send_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Pretty print JSON for better readability
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        self.wfile.write(json_str.encode('utf-8'))
    
    def _send_error(self, status_code, message):
        """Send error response"""
        error_data = {
            "status": "error",
            "message": message
        }
        self._send_response(status_code, error_data)
