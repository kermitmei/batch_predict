from fastapi import Body
from pydantic import BaseModel


class PromptBatchDTO(BaseModel):
    """
    分析用户资料
    """
    prompt_list: list[str] = Body(title='提示词列表', description='批量推理请求的prompt列表')
