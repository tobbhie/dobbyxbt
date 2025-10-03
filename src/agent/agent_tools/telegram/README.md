# DobbyXBT Telegram Bot

A powerful AI-powered DobbyXBT Telegram bot that provides real-time crypto data, market insights, and intelligent responses using CryptoRank API v2 integration.

## Features

- 🚀 **AI-Powered Responses**: Intelligent natural language processing for crypto queries
- 💰 **Real-Time Prices**: Get current cryptocurrency prices and market data
- 🔥 **Trending Assets**: Hot cryptocurrencies and market movers
- 🏦 **Investment Data**: Top crypto investors and funds information
- 🎯 **Drophunting**: Airdrop activities and reward opportunities
- 🤖 **Natural Language**: Understands crypto requests in plain English
- 🛡️ **Robust Error Handling**: Comprehensive error handling with user-friendly messages
- ⚙️ **Highly Configurable**: Extensive configuration options for crypto services
- 🔌 **CryptoRank API v2 Integration**: Full integration with CryptoRank's comprehensive crypto data

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Required: Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Required: CryptoRank API Configuration
CRYPTORANK_API_KEY=your_cryptorank_api_key_here

# Optional: AI Model Configuration (for smart responses)
MODEL_API_KEY=your_fireworks_ai_api_key_here

```

### Getting API Keys

#### 1. Telegram Bot Token
1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather
3. Send `/newbot` command
4. Follow the instructions to create your bot
5. Copy the bot token provided by BotFather

#### 2. CryptoRank API Key
1. Visit [CryptoRank.io](https://cryptorank.io)
2. Sign up for an account
3. Navigate to API section
4. Generate your API key
5. Add the key to your `.env` file

#### 3. AI Model API Key (Optional)
1. Visit [Fireworks AI](https://fireworks.ai)
2. Sign up for an account
3. Generate your API key
4. Add the key to your `.env` file for intelligent responses

### Configuration Options

The `telegram_config.py` file contains crypto-specific configuration options:

- **Crypto Keywords**: Keywords that trigger crypto-specific responses
- **CryptoRank API Settings**: Timeout, retries, and caching for API calls
- **Price Alert Settings**: Thresholds and notification preferences
- **Trending Settings**: Market cap filters and display limits
- **Rate Limiting**: Enhanced rate limiting for DobbyXBT Bot usage
- **Crypto Emojis**: Customizable emoji mapping for crypto symbols

## Usage

### Local Development

To run the bot locally:

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the bot
python -m src.agent.agent_tools.telegram
```

### Render Deployment

The bot is configured for deployment on Render:

1. **Connect Repository**: Link your GitHub repository to Render
2. **Set Environment Variables**: Add `TELEGRAM_BOT_TOKEN`, `CRYPTORANK_API_KEY`, and optionally `MODEL_API_KEY`
3. **Deploy**: Render will automatically build and deploy your bot
4. **Set Webhook**: Visit `https://your-app.onrender.com/set_webhook` to configure the Telegram webhook

See [RENDER_DEPLOYMENT.md](../../../RENDER_DEPLOYMENT.md) for detailed deployment instructions.

## Bot Commands

### Main Commands
- `/start` - Welcome message with interactive menu
- `/help` - Show all available commands and usage instructions

### Price Commands
- `/price BTC` - Get Bitcoin price
- `/price BTC,ETH` - Compare multiple cryptocurrency prices
- `/price bitcoin` - Natural language price requests

### Trending Commands
- `/trending` - Trending cryptocurrencies by market cap
- `/trending gainers` - Top gainers (24h)
- `/trending losers` - Top losers (24h)

### Investment Data Commands
- `/funds` - Top crypto investors and funds
- `/funds tier1` - Tier 1 investment funds only

### Drophunting Commands
- `/drophunting` - Latest airdrop activities and rewards
- `/drophunting active` - Active airdrop opportunities only

## Natural Language Examples

Users can interact with the bot using natural language:

### Price Requests
- "What's the price of Bitcoin?"
- "How much is Ethereum worth?"
- "Show me BTC and ETH prices"
- "What's happening with Solana?"

### Market Requests
- "Show me trending cryptocurrencies"
- "What are the top gainers today?"
- "Which cryptos are hot right now?"

### Investment Requests
- "Top crypto investors"
- "Show me investment funds"
- "Who are the biggest crypto VCs?"

### Drophunting Requests
- "Show me airdrop opportunities"
- "Latest drophunting activities"
- "Any new crypto rewards?"

## API Integration

### CryptoRank API v2 Endpoints

- **`/v2/currencies`**: Real-time cryptocurrency prices and market data
- **`/v2/funds/map`**: Crypto investors and funds information
- **`/v2/drophunting/activities`**: Airdrop activities and rewards (Premium)

### Features
- **Real-time Data**: Live cryptocurrency prices and market updates
- **Market Analytics**: Trending assets and market movers
- **Investment Intelligence**: Top crypto funds and investor data
- **Airdrop Tracking**: Latest drophunting opportunities

## Deployment Architecture

### Local Mode (Polling)
- Uses Telegram's long polling for development
- Suitable for testing and local development
- Requires continuous server uptime

### Production Mode (Webhook)
- Webhook architecture for Render deployment
- Event-driven, cost-effective scaling
- Self-configuring webhook management
- Production-ready error handling

### Webhook Management
- **Set Webhook**: `/set_webhook`
- **Check Status**: `/webhook_info`
- **Health Check**: `/`

## Error Handling

The bot includes comprehensive error handling:

- **API Rate Limiting**: Automatic retry with exponential backoff
- **Network Timeouts**: Robust timeout configuration
- **Invalid Requests**: User-friendly error messages
- **Missing Data**: Graceful fallbacks and alternatives
- **Premium API Limits**: Cheeky error messages for paid features

## Development

### Project Structure
```
src/agent/agent_tools/telegram/
├── telegram_bot.py      # Main bot implementation
├── telegram_config.py   # Configuration settings
├── webhook_bot.py       # Webhook-specific functionality
└── __main__.py         # Entry point for running the bot
```

### Key Components
1. **Telegram Bot**: Core bot functionality and command handling
2. **CryptoRank Integration**: API client for crypto data
3. **AI Model**: Natural language processing for intelligent responses
4. **Webhook System**: Serverless deployment architecture

## Attribution

Created by [pipsandbills](https://x.com/pipsandbills)

## License

This project is licensed under the MIT License - see the LICENSE file for details.