# 🤖 Telegram Bot Setup Guide

## Quick Start

### 1. Tạo Telegram Bot

1. Message `@BotFather` trên Telegram
2. Gửi `/newbot`
3. Đặt tên cho bot (ví dụ: "AI Work OS Bot") 
4. Đặt username cho bot (ví dụ: "ai_work_os_bot")
5. Copy `BOT_TOKEN` được BotFather cung cấp

### 2. Cấu hình Environment

```bash
# Copy và edit .env
cp .env.example .env

# Thêm Telegram bot token
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxyz
```

### 3. Chạy với Docker Compose (Khuyến nghị)

```bash
# Chạy full stack: App + Bot + Redis + Celery
docker-compose -f docker-compose.telegram.yml up -d
```

### 4. Hoặc chạy từng component riêng

```bash
# Terminal 1: Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Terminal 2: Main App
python -m uvicorn src.main:app --reload --port 8000

# Terminal 3: Celery Worker
celery -A src.services.background_service worker --loglevel=info

# Terminal 4: Telegram Bot
python telegram_bot.py
```

## 📱 Sử dụng Bot

### Lệnh cơ bản

- `/start` - Khởi động bot và xem hướng dẫn
- `/help` - Hướng dẫn chi tiết
- `/add <text>` - Tạo tasks từ văn bản
- `/tasks` - Xem danh sách tasks của bạn
- `/ask <question>` - Hỏi đáp về documents
- `/status` - Tổng quan tasks

### Auto-processing

Gửi bất kỳ tin nhắn nào để bot tự động:
- Phân tích văn bản
- Trích xuất action items
- Tạo tasks với due date và owner
- Lưu để search sau này

### Ví dụ

```
User: "Meeting với client ngày mai 2pm. Cần prepare slides về quarterly report và gửi contract cho legal team review trước thứ 6."

Bot: ✅ Đã tạo 2 tasks mới!

📝 Tóm tắt: Meeting client ngày mai, cần chuẩn bị slides quarterly report và gửi contract review.

Dùng /tasks để xem chi tiết!
```

## 🏗 Architecture

```
Telegram User
    ↓
Telegram Bot (polling)
    ↓
Background Service (Celery)
    ↓
Document Service (AI processing)
    ↓
Database (SQLite)
```

### Message Flow

1. User gửi message → Telegram Bot
2. Bot tạo MessageData → Queue vào Celery
3. Celery Worker xử lý document → Extract tasks
4. Bot reply với kết quả

### Background Processing

- **High Priority**: User messages từ Telegram
- **Normal Priority**: Batch processing, scheduled tasks
- **Low Priority**: Cleanup, maintenance

## 🔧 Configuration

### Bot Settings

```env
# Required
TELEGRAM_BOT_TOKEN=your-bot-token

# Optional
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook/telegram
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Celery Settings

```python
# In background_service.py
celery_app.conf.update(
    task_serializer='json',
    timezone='UTC',
    task_routes={
        'process_message_async': {'queue': 'high'},
        'cleanup_old_tasks': {'queue': 'low'},
    }
)
```

## 🚀 Production Deployment

### Docker Compose Production

```bash
# Production với monitoring
docker-compose -f docker-compose.telegram.yml -f docker-compose.prod.yml up -d
```

### Health Checks

```bash
# Check services
docker-compose ps

# Check logs
docker-compose logs telegram-bot
docker-compose logs celery-worker

# Check Redis
docker-compose exec redis redis-cli ping
```

### Monitoring

```bash
# Celery monitoring
celery -A src.services.background_service inspect active
celery -A src.services.background_service inspect stats

# Bot status
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"
```

## 🛠 Development

### Local Development Setup

```bash
# Install dependencies
pip install python-telegram-bot celery redis

# Run Redis
docker run -d -p 6379:6379 redis:7-alpine

# Run in separate terminals:
celery -A src.services.background_service worker --loglevel=debug
python telegram_bot.py
```

### Testing Bot

```bash
# Test bot connection
python -c "
from telegram import Bot
bot = Bot('YOUR_BOT_TOKEN')
print(bot.get_me())
"

# Test message processing
python -c "
from src.services.background_service import process_message_async
from src.core.types import TelegramMessageData
# ... test code
"
```

### Adding New Commands

1. Thêm handler trong `src/integrations/telegram/bot.py`:

```python
async def new_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Command logic
    pass

# Register trong initialize()
self.application.add_handler(CommandHandler("newcmd", self.new_command))
```

2. Update help text và documentation

## 🚨 Troubleshooting

### Common Issues

**Bot không response?**
```bash
# Check bot token
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Check logs
docker-compose logs telegram-bot
```

**Celery tasks không chạy?**
```bash
# Check Redis connection
redis-cli ping

# Check worker status
celery -A src.services.background_service inspect ping
```

**Database errors?**
```bash
# Check database file permissions
ls -la data/
chmod 666 data/app.db
```

### Performance Issues

**Slow response times?**
- Increase Celery worker concurrency
- Add more worker processes
- Optimize database queries

**High memory usage?**
- Set Celery memory limits
- Implement task result cleanup
- Monitor Redis memory usage

## 📊 Metrics & Monitoring

### Key Metrics

- Message processing time
- Task success/failure rates  
- Active user count
- Database size growth

### Monitoring Setup

```bash
# Redis monitoring
redis-cli --latency-history -i 1

# Celery monitoring
celery -A src.services.background_service events

# Application logs
docker-compose logs -f --tail=100
```

## 🔐 Security Considerations

1. **Bot Token Security**
   - Never commit tokens to git
   - Use environment variables
   - Rotate tokens regularly

2. **Rate Limiting**
   - Built-in rate limiting in routes
   - Redis-based user rate limiting
   - Message flood protection

3. **Data Privacy**
   - User messages are processed locally
   - No data sent to third parties except OpenAI API
   - Implement data retention policies

4. **Access Control**
   - Bot responds to all users by default
   - Consider user whitelisting for private deployments
   - Monitor usage patterns

## 🎯 Next Steps

Sau khi bot chạy ổn định:

1. **Email Integration** (tuần tiếp theo)
2. **Web UI improvements** (dark mode, shortcuts)
3. **Smart notifications** (overdue tasks, reminders)
4. **Advanced AI features** (task prioritization, suggestions)

---

**🎉 Telegram Bot đã sẵn sàng cho Phase 3!**