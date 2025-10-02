"""
Script to setup webhook for Telegram bot on Vercel
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_webhook():
    """Setup webhook for Telegram bot"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        return False
    
    if not webhook_url:
        print("❌ WEBHOOK_URL not found in environment variables")
        print("💡 Set WEBHOOK_URL to your Vercel deployment URL + /api/webhook")
        print("   Example: https://your-app.vercel.app/api/webhook")
        return False
    
    # Set webhook
    url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    data = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query"]
    }
    
    try:
        response = requests.post(url, json=data)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Webhook set successfully!")
            print(f"🔗 Webhook URL: {webhook_url}")
            return True
        else:
            print(f"❌ Failed to set webhook: {result.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting webhook: {str(e)}")
        return False

def remove_webhook():
    """Remove webhook for Telegram bot"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    
    try:
        response = requests.post(url)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Webhook removed successfully!")
            return True
        else:
            print(f"❌ Failed to remove webhook: {result.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error removing webhook: {str(e)}")
        return False

def get_webhook_info():
    """Get current webhook information"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    
    try:
        response = requests.get(url)
        result = response.json()
        
        if result.get("ok"):
            webhook_info = result.get("result", {})
            print("📋 Current webhook info:")
            print(f"   URL: {webhook_info.get('url', 'Not set')}")
            print(f"   Pending updates: {webhook_info.get('pending_update_count', 0)}")
            print(f"   Last error: {webhook_info.get('last_error_message', 'None')}")
            return True
        else:
            print(f"❌ Failed to get webhook info: {result.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting webhook info: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "set":
            setup_webhook()
        elif command == "remove":
            remove_webhook()
        elif command == "info":
            get_webhook_info()
        else:
            print("Usage: python setup_webhook.py [set|remove|info]")
    else:
        print("🚀 Telegram Bot Webhook Setup")
        print("Usage: python setup_webhook.py [set|remove|info]")
        print()
        print("Commands:")
        print("  set    - Set webhook URL")
        print("  remove - Remove webhook")
        print("  info   - Get webhook information")
