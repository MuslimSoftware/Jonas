from .chat_model import Chat
from .message_model import Message
from .screenshot_model import Screenshot
from .context_item_model import ContextItem

# Rebuild models after both are imported to resolve forward references
Chat.model_rebuild()
Message.model_rebuild()
Screenshot.model_rebuild()
ContextItem.model_rebuild()

# Also rebuild user model if it might have forward refs
from app.features.user.models import User
User.model_rebuild()

__all__ = [
    "Chat",
    "Message",
    "Screenshot",
    "ContextItem"
] 