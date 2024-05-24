class LlmService:

    @classmethod
    def get_instance(cls, model_name: str, temperature: float = 0.5, max_tokens: int = 1024):
        if model_name == 'chatglm3-6b-32k':
            from core.main.services.chatglm3_service import ChatGLM3Service
            return ChatGLM3Service(model_name, temperature, max_tokens)
        elif model_name == 'internlm-chat-20b':
            from core.main.services.internlm_chat_20b_service import InternlmChat20bService

