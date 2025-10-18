# 🚀 Getting Started

This guide will help you set up and run BotDealsGarant on your server.

## 📋 Prerequisites

- **Python 3.9+** - Modern Python version
- **Git** - For cloning the repository
- **Telegram Bot Token** - From [@BotFather](https://t.me/BotFather)
- **CryptoBot API Key** - From [CryptoPay](https://t.me/CryptoBot)

## 📥 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/VozdyXxx/BotDealsGarant.git
cd BotDealsGarant
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements
```

### 4. Configure Environment
Copy the example environment file and fill in your credentials:
```bash
# Create .env file
cp .env.example .env
```

Edit `.env` file with your credentials:
```env
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here

# Admin Configuration
ROOT_ADMIN_ID=your_telegram_user_id

# CryptoBot API Configuration
CRYPTOBOT_API_KEY=your_cryptobot_api_key
CRYPTOBOT_TESTNET_URL=https://testnet-pay.crypt.bot/api
```

## 🔧 Getting API Keys

### Telegram Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` command
3. Follow the prompts to create your bot
4. Copy the token and add to `.env`

### Your User ID
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your user ID for `ROOT_ADMIN_ID`

### CryptoBot API Key
1. Open [@CryptoBot](https://t.me/CryptoBot)
2. Go to Crypto Pay section
3. Create new app and get API key
4. Add key to `.env`

## 🚀 Running the Bot

### Development Mode
```bash
python main.py
```

### Production with PM2
```bash
# Install PM2
npm install -g pm2

# Start bot with PM2
pm2 start main.py --name "botdealsgarant" --interpreter python3

# Save PM2 configuration
pm2 save
pm2 startup
```

## ✅ Verification

After starting the bot, verify it's working:

1. **Check console output** - Should show "Bot started successfully"
2. **Test bot commands** - Send `/start` to your bot
3. **Check admin panel** - Use `/admin` command
4. **Test payments** - Try creating a test transaction

## 🔧 Common Issues

### Bot Token Invalid
- Verify token in `.env` file
- Check token format (should be like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Permission Denied
- Make sure Python has execution permissions
- Check virtual environment activation

### Database Errors
- Ensure SQLite is available
- Check file permissions in project directory

## 📚 Next Steps

- [Configuration Guide](Configuration) - Customize bot settings
- [User Guide](User-Guide) - Learn bot features
- [Security Guide](Security) - Implement security best practices

---

Need help? [Ask a question](https://github.com/VozdyXxx/BotDealsGarant/issues/new?template=question.md) or contact [@Breathe_VozdyX](https://t.me/Breathe_VozdyX)