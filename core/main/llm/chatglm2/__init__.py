import os

import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel

from ottawa.core.main.llm import LLM


class ChatGLM2(LLM):
    """
    # 在OpenAI的API中，max_tokens 等价于 HuggingFace 的 max_new_tokens 而不是 max_length，。
    # 例如，对于6b模型，设置max_tokens = 8192，则会报错，因为扣除历史记录和提示词后，模型不能输出那么>多的tokens。
    """
    name: str = 'ChatGLM2-6b-32k'
    tokenizer: AutoTokenizer = None
    model: AutoModel = None
    embedding: SentenceTransformer = None

    def __init__(self, pretrained_model_name_or_path: str, embedding_model_path: str, cuda_devices: str = None):
        """
        :param cuda_devices: 运行GPU编号, '0,1'
        """
        # 多GPU环境指定运行在哪个GPU
        DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path=pretrained_model_name_or_path, trust_remote_code=True)
        if 'cuda' in DEVICE:  # AMD, NVIDIA GPU can use Half Precision
            if cuda_devices:
                # os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"
                os.environ["CUDA_VISIBLE_DEVICES"] = cuda_devices
            model = AutoModel.from_pretrained(pretrained_model_name_or_path=pretrained_model_name_or_path, trust_remote_code=True).to(DEVICE).eval()
        else:  # CPU, Intel GPU and other GPU can use Float16 Precision Only
            model = AutoModel.from_pretrained(pretrained_model_name_or_path=pretrained_model_name_or_path, trust_remote_code=True).float().to(DEVICE).eval()
        # 多显卡支持，使用下面两行代替上面一行，将num_gpus改为你实际的显卡数量
        # from utils import load_model_on_gpus
        # model = load_model_on_gpus("THUDM/chatglm2-6b", num_gpus=2)
        self.model = model.eval()
