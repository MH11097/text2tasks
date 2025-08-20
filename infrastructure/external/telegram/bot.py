"""Telegram Bot integration với clean architecture"""

import logging
from typing import Dict, Any, Optional
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
from datetime import datetime

from ...services.document_service import DocumentService
from ...services.task_service import TaskService
from ...core.types import SourceType, TelegramMessageData, ProcessingResult
from ...core.exceptions import IntegrationException
from ...config import settings
from ...llm_client import LLMClient

logger = logging.getLogger(__name__)

class TelegramBot:
    """
    Telegram Bot với clean architecture
    Single Responsibility: Handle telegram integration only
    """
    
    def __init__(self, token: str):
        self.token = token
        self.application = None
        self.document_service = DocumentService()
        self.task_service = TaskService()
        self.llm_client = LLMClient()
        
    async def initialize(self):
        """Initialize bot application"""
        try:
            self.application = Application.builder().token(self.token).build()
            
            # Register handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("add", self.add_command))
            self.application.add_handler(CommandHandler("tasks", self.tasks_command))
            self.application.add_handler(CommandHandler("ask", self.ask_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(CommandHandler("done", self.mark_done_command))
            self.application.add_handler(CommandHandler("progress", self.mark_progress_command))
            self.application.add_handler(CommandHandler("block", self.mark_blocked_command))
            
            # Handle text messages (auto-extract tasks)
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message)
            )
            
            # Handle callback queries for inline buttons
            from telegram.ext import CallbackQueryHandler
            self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
            
            logger.info("Telegram bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize telegram bot: {e}")
            raise IntegrationException(f"Bot initialization failed: {e}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 **AI Work OS Bot**

Chào mừng! Bot này giúp bạn quản lý công việc thông minh.

**Lệnh có sẵn:**
• `/add <text>` - Tạo tasks từ văn bản
• `/tasks` - Xem danh sách tasks (có số thứ tự)
• `/done <số>` - Hoàn thành task
• `/ask <question>` - Hỏi đáp về documents
• `/status` - Tổng quan hệ thống
• `/help` - Hướng dẫn chi tiết

**Hoặc đơn giản:**
Gửi tin nhắn bất kỳ để tự động tạo tasks!

Ví dụ: "Meeting ngày mai 2pm, cần chuẩn bị slides và gửi agenda cho team"
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
        # Log user interaction
        logger.info(
            "New user started bot",
            extra={
                "user_id": update.effective_user.id,
                "username": update.effective_user.username
            }
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
📖 **Hướng dẫn sử dụng AI Work OS Bot**

**1. Tự động tạo tasks:**
Chỉ cần gửi tin nhắn bất kỳ, bot sẽ tự động phân tích và tạo tasks.

*Ví dụ:*
"Cuộc họp với client vào thứ 5 lúc 2pm. Cần prepare presentation và review contract trước đó."

**2. Lệnh cụ thể:**

• `/add <văn bản>` 
  Tạo tasks từ văn bản cụ thể
  
• `/tasks [status]`
  Xem tasks (all/new/progress/done/blocked)
  
• `/ask <câu hỏi>`
  Hỏi đáp về documents đã lưu
  
• `/status`
  Xem tổng quan tasks và hệ thống
  
• `/done <số>` - Đánh dấu task hoàn thành
• `/progress <số>` - Đánh dấu task đang làm  
• `/block <số>` - Đánh dấu task bị block

**3. Tính năng thông minh:**
✅ Tự động nhận diện người làm
✅ Tự động detect deadline  
✅ Phân loại priority
✅ Support tiếng Việt hoàn toàn

**Tips:**
- Viết rõ ràng để bot hiểu chính xác
- Mention tên người và thời gian để tự động assign
- Bot lưu tất cả để search sau này
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def add_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add command"""
        if not context.args:
            await update.message.reply_text("❌ Cần cung cấp văn bản để tạo tasks.\n\nVí dụ: `/add Meeting ngày mai, cần chuẩn bị slides`")
            return
        
        text = " ".join(context.args)
        await self._process_user_text(update, text)
    
    async def tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tasks command"""
        try:
            # Parse status filter nếu có
            status_filter = None
            if context.args:
                status_arg = context.args[0].lower()
                status_mapping = {
                    "new": "new",
                    "progress": "in_progress", 
                    "blocked": "blocked",
                    "done": "done"
                }
                status_filter = status_mapping.get(status_arg)
            
            # Get tasks cho user này
            user_id = str(update.effective_user.id)
            tasks = await self.task_service.get_tasks(
                source_type_filter=SourceType.TELEGRAM.value,
                limit=20
            )
            
            # Filter tasks từ user này (check source_id trong document)
            user_tasks = []
            for task in tasks:
                # Cần check document để verify source_id
                doc = await self.document_service.get_document_by_id(int(task["source_doc_id"]))
                if doc and doc.source_id == user_id:
                    user_tasks.append(task)
            
            if not user_tasks:
                await update.message.reply_text("📝 Chưa có tasks nào. Gửi tin nhắn để tạo tasks tự động!")
                return
            
            # Format message
            message = f"📋 **Tasks của bạn** ({len(user_tasks)} tasks)\n\n"
            
            status_emoji = {
                "new": "🆕",
                "in_progress": "⏳", 
                "blocked": "🚫",
                "done": "✅"
            }
            
            for i, task in enumerate(user_tasks[:10], 1):  # Show max 10 with numbers
                emoji = status_emoji.get(task["status"], "📌")
                owner = f"👤 {task['owner']}" if task["owner"] else ""
                due = f"📅 {task['due_date']}" if task["due_date"] else ""
                
                message += f"{i}. {emoji} **{task['title']}**\n"
                if owner or due:
                    message += f"   {owner} {due}\n"
                message += "\n"
            
            if len(user_tasks) > 10:
                message += f"... và {len(user_tasks) - 10} tasks khác"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Tasks command failed: {e}")
            await update.message.reply_text("❌ Lỗi khi lấy danh sách tasks. Vui lòng thử lại.")
    
    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask command"""
        if not context.args:
            await update.message.reply_text("❓ Cần đặt câu hỏi.\n\nVí dụ: `/ask Database schema thế nào rồi?`")
            return
        
        question = " ".join(context.args)
        
        try:
            await update.message.reply_text("🔍 Đang tìm kiếm thông tin...")
            
            # Search documents
            user_id = str(update.effective_user.id)
            relevant_docs = await self.document_service.search_documents_by_similarity(
                question,
                top_k=6,
                source_type_filter=SourceType.TELEGRAM
            )
            
            # Filter docs from this user
            user_docs = []
            for doc in relevant_docs:
                if doc.get("source_id") == user_id:
                    user_docs.append(doc)
            
            if not user_docs:
                await update.message.reply_text("🤷‍♂️ Không tìm thấy thông tin liên quan trong dữ liệu của bạn.")
                return
            
            # Create context
            context_text = "\n\n".join([doc["text"][:500] for doc in user_docs[:3]])
            
            # Get answer from LLM
            result = await self.llm_client.answer_question(question, context_text)
            
            # Format response
            message = f"💡 **Câu trả lời:**\n{result['answer']}\n\n"
            
            if result.get('suggested_next_steps'):
                message += "**Gợi ý tiếp theo:**\n"
                for step in result['suggested_next_steps']:
                    message += f"• {step}\n"
            
            message += f"\n📊 *Tìm thấy từ {len(user_docs)} documents*"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ask command failed: {e}")
            await update.message.reply_text("❌ Lỗi khi xử lý câu hỏi. Vui lòng thử lại.")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            # Get user's task counts
            user_id = str(update.effective_user.id)
            user_tasks = await self._get_user_tasks(user_id)
            
            # Count by status
            counts = {"new": 0, "in_progress": 0, "blocked": 0, "done": 0}
            for task in user_tasks:
                status = task["status"]
                if status in counts:
                    counts[status] += 1
            
            # Format message
            total = sum(counts.values())
            message = f"📊 **Tổng quan Tasks của bạn**\n\n"
            message += f"📈 Tổng cộng: **{total}** tasks\n\n"
            message += f"🆕 Mới: **{counts['new']}**\n"
            message += f"⏳ Đang làm: **{counts['in_progress']}**\n"
            message += f"🚫 Bị block: **{counts['blocked']}**\n"
            message += f"✅ Hoàn thành: **{counts['done']}**\n\n"
            
            # Active tasks percentage
            active = counts['new'] + counts['in_progress']
            if total > 0:
                active_pct = round(active / total * 100)
                message += f"🔥 Đang active: **{active_pct}%**"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Status command failed: {e}")
            await update.message.reply_text("❌ Lỗi khi lấy thống kê. Vui lòng thử lại.")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages - auto extract tasks"""
        text = update.message.text
        
        # Skip if message too short
        if len(text.strip()) < 10:
            await update.message.reply_text("📝 Tin nhắn hơi ngắn. Gửi thêm chi tiết để tạo tasks tự động!")
            return
        
        await self._process_user_text(update, text)
    
    async def mark_done_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /done command to mark task as completed"""
        await self._update_task_status(update, context, "done", "✅ Đã đánh dấu task hoàn thành!")
    
    async def mark_progress_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /progress command to mark task as in progress"""
        await self._update_task_status(update, context, "in_progress", "⏳ Đã đánh dấu task đang thực hiện!")
    
    async def mark_blocked_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /block command to mark task as blocked"""
        await self._update_task_status(update, context, "blocked", "🚫 Đã đánh dấu task bị block!")
    
    async def _update_task_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE, status: str, success_msg: str):
        """Helper to update task status by task number"""
        if not context.args:
            await update.message.reply_text(f"❌ Cần cung cấp số thứ tự task.\n\nVí dụ: `/{status.replace('_', '')} 1`")
            return
        
        try:
            task_number = int(context.args[0])
            user_id = str(update.effective_user.id)
            user_tasks = await self._get_user_tasks(user_id)
            
            if task_number < 1 or task_number > len(user_tasks):
                await update.message.reply_text(f"❌ Task số {task_number} không tồn tại. Dùng `/tasks` để xem danh sách.")
                return
            
            task = user_tasks[task_number - 1]
            task_id = int(task["id"])
            
            # Update task
            await self.task_service.update_task(task_id=task_id, status=status)
            
            await update.message.reply_text(f"{success_msg}\n\n📝 **{task['title']}**")
            
        except ValueError:
            await update.message.reply_text("❌ Số task không hợp lệ.")
        except Exception as e:
            logger.error(f"Task status update failed: {e}")
            await update.message.reply_text("❌ Lỗi khi cập nhật task.")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Parse callback data: action_taskid
            action, task_id = query.data.split('_', 1)
            task_id = int(task_id)
            
            if action == "done":
                await self.task_service.update_task(task_id=task_id, status="done")
                await query.edit_message_text("✅ Task đã hoàn thành!")
            elif action == "progress":
                await self.task_service.update_task(task_id=task_id, status="in_progress")
                await query.edit_message_text("⏳ Task đang thực hiện!")
            elif action == "block":
                await self.task_service.update_task(task_id=task_id, status="blocked")
                await query.edit_message_text("🚫 Task bị block!")
                
        except Exception as e:
            logger.error(f"Callback query failed: {e}")
            await query.edit_message_text("❌ Lỗi khi cập nhật task.")
    
    async def _process_user_text(self, update: Update, text: str):
        """
        Process user text và tạo tasks
        DRY: Reusable text processing logic
        """
        try:
            await update.message.reply_text("⚡ Đang phân tích và tạo tasks...")
            
            # Create message data
            user_id = str(update.effective_user.id)
            message_data = TelegramMessageData(
                text=text,
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                user_id=update.effective_user.id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name
            )
            
            # Process document
            result = await self.document_service.process_document(
                text=text,
                source="chat",
                source_type=SourceType.TELEGRAM,
                source_id=user_id,
                metadata=message_data.dict()
            )
            
            if not result.success:
                await update.message.reply_text(f"❌ Lỗi khi xử lý: {result.error_message}")
                return
            
            # Format success message
            if result.actions_count > 0:
                message = f"✅ **Đã tạo {result.actions_count} tasks mới!**\n\n"
                message += f"📝 **Tóm tắt:** {result.summary}\n\n"
                message += "Dùng `/tasks` để xem chi tiết hoặc `/ask` để hỏi thêm!"
            else:
                message = f"📄 **Đã lưu document**\n\n"
                message += f"📝 **Tóm tắt:** {result.summary}\n\n"
                message += "Không tìm thấy action items cụ thể. Dùng `/ask` để hỏi về nội dung này!"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
            # Log successful processing
            logger.info(
                "Text message processed successfully", 
                extra={
                    "user_id": update.effective_user.id,
                    "document_id": result.document_id,
                    "actions_count": result.actions_count
                }
            )
            
        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            await update.message.reply_text("❌ Có lỗi khi xử lý tin nhắn. Vui lòng thử lại hoặc liên hệ admin.")
    
    async def _get_user_tasks(self, user_id: str, limit: int = 100):
        """Get all tasks for a specific user"""
        all_tasks = await self.task_service.get_tasks(
            source_type_filter=SourceType.TELEGRAM.value,
            limit=limit
        )
        
        user_tasks = []
        for task in all_tasks:
            doc = await self.document_service.get_document_by_id(int(task["source_doc_id"]))
            if doc and doc.source_id == user_id:
                user_tasks.append(task)
        
        return user_tasks
    
    async def start_polling(self):
        """Start bot polling"""
        if not self.application:
            raise IntegrationException("Bot not initialized")
        
        try:
            logger.info("Starting Telegram bot polling...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Telegram bot is running!")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Bot polling failed: {e}")
            raise IntegrationException(f"Polling failed: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop bot"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram bot stopped")