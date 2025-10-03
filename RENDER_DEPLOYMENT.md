# DobbyXBT Bot - Render Deployment Guide

## 🚀 Deploy to Render

### Prerequisites
- GitHub repository with your bot code
- Telegram bot token from @BotFather
- CryptoRank API key (optional but recommended)
- Fireworks AI API key (optional for smart responses)

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Connect your GitHub repository

### Step 2: Create Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Choose the repository containing your bot

### Step 3: Configure Service
**Basic Settings:**
- **Name**: `dobbyxbt-bot` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `main` (or your default branch)

**Build & Deploy:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`

### Step 4: Set Environment Variables
In the Render dashboard, go to "Environment" tab and add:

```
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
CRYPTORANK_API_KEY=your_cryptorank_api_key
MODEL_API_KEY=your_fireworks_ai_api_key
```

### Step 5: Deploy
1. Click "Create Web Service"
2. Wait for deployment to complete
3. Note your service URL (e.g., `https://dobbyxbt.onrender.com`)

### Step 6: Set Webhook
After deployment, visit these URLs to configure your bot:

1. **Set Webhook**: `https://your-app.onrender.com/set_webhook`
2. **Check Webhook Info**: `https://your-app.onrender.com/webhook_info`
3. **Health Check**: `https://your-app.onrender.com/`

### Step 7: Test Your Bot
1. Open Telegram and find your bot
2. Send `/start` to test
3. Try commands like `/price BTC`, `/trending`, `/funds`

## 🔧 Local Development

### Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN=your_token
export CRYPTORANK_API_KEY=your_key
export MODEL_API_KEY=your_ai_key

# Run the bot
python app.py
```

### Test Webhook Locally
Use ngrok to expose your local server:
```bash
# Install ngrok
npm install -g ngrok

# Run your bot
python app.py

# In another terminal, expose port 5000
ngrok http 5000

# Use the ngrok URL to set webhook
curl "https://your-ngrok-url.ngrok.io/set_webhook"
```

## 📋 Bot Commands

- `/start` - Welcome message with menu
- `/help` - Show all commands
- `/price <symbol>` - Get crypto price (e.g., `/price BTC`)
- `/trending` - Top trending cryptocurrencies
- `/funds` - Top crypto investment funds
- `/drophunting` - Airdrop activities

## 🤖 Natural Language

Users can chat naturally:
- "What's the price of Bitcoin?"
- "Show me trending cryptos"
- "Top crypto investors"
- "Any new airdrops?"

## 🛠️ Troubleshooting

### Bot Not Responding
1. Check webhook is set: `https://your-app.onrender.com/webhook_info`
2. Verify environment variables are set
3. Check Render logs for errors

### API Errors
1. Ensure `CRYPTORANK_API_KEY` is set
2. Check API key is valid and has sufficient quota
3. For drophunting endpoint, you may need a paid API key

### Deployment Issues
1. Check build logs in Render dashboard
2. Ensure all dependencies are in `requirements.txt`
3. Verify Python version compatibility

## 📞 Support

Created by [pipsandbills](https://x.com/pipsandbills)

For issues or questions:
- Check the logs in Render dashboard
- Verify all environment variables are set
- Test locally first before deploying
