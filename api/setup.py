"""
Vercel API endpoint for webhook management
Access via: https://your-app.vercel.app/api/setup?action=set
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class handler(BaseHTTPRequestHandler):
    """Vercel API handler for webhook management"""
    
    def do_GET(self):
        """Handle GET requests for webhook management"""
        try:
            # Parse URL and query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            action = query_params.get('action', [''])[0].lower()
            
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not bot_token:
                self._send_error(400, "TELEGRAM_BOT_TOKEN not configured")
                return
            
            # Get the current domain from headers
            host = self.headers.get('Host', 'dobbyxbt.vercel.app')
            webhook_url = f"https://{host}/api/webhook"
            
            if action == 'set':
                result = self._set_webhook(bot_token, webhook_url)
            elif action == 'remove':
                result = self._remove_webhook(bot_token)
            elif action == 'info':
                result = self._get_webhook_info(bot_token)
            else:
                result = self._show_help(webhook_url)
            
            self._send_response(200, result)
            
        except Exception as e:
            self._send_error(500, f"Error: {str(e)}")
    
    def _set_webhook(self, bot_token, webhook_url):
        """Set webhook for the bot"""
        url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        data = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"]
        }
        
        response = requests.post(url, json=data)
        result = response.json()
        
        if result.get("ok"):
            return {
                "status": "success",
                "message": "Webhook set successfully!",
                "webhook_url": webhook_url,
                "description": result.get("description", "")
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to set webhook: {result.get('description', 'Unknown error')}"
            }
    
    def _remove_webhook(self, bot_token):
        """Remove webhook for the bot"""
        url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        
        response = requests.post(url)
        result = response.json()
        
        if result.get("ok"):
            return {
                "status": "success",
                "message": "Webhook removed successfully!",
                "description": result.get("description", "")
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to remove webhook: {result.get('description', 'Unknown error')}"
            }
    
    def _get_webhook_info(self, bot_token):
        """Get current webhook information"""
        url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        
        response = requests.get(url)
        result = response.json()
        
        if result.get("ok"):
            webhook_info = result.get("result", {})
            return {
                "status": "success",
                "webhook_info": {
                    "url": webhook_info.get("url", "Not set"),
                    "pending_updates": webhook_info.get("pending_update_count", 0),
                    "last_error": webhook_info.get("last_error_message", "None"),
                    "last_error_date": webhook_info.get("last_error_date", None)
                }
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to get webhook info: {result.get('description', 'Unknown error')}"
            }
    
    def _show_help(self, webhook_url):
        """Show help information"""
        return {
            "status": "help",
            "message": "Telegram Bot Webhook Management",
            "webhook_url": webhook_url,
            "endpoints": {
                "set_webhook": f"GET /api/setup?action=set",
                "remove_webhook": f"GET /api/setup?action=remove", 
                "webhook_info": f"GET /api/setup?action=info",
                "help": f"GET /api/setup"
            },
            "instructions": [
                "1. First deploy your bot to Vercel",
                "2. Visit /api/setup?action=set to configure webhook",
                "3. Test your bot by sending /start on Telegram",
                "4. Use /api/setup?action=info to check status"
            ]
        }
    
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
