import os

import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel, AutoModelForCausalLM

from ottawa.core.main.llm import LLM


class InternLMChat20B(LLM):
    """
    # 在OpenAI的API中，max_tokens 等价于 HuggingFace 的 max_new_tokens 而不是 max_length，。
    # 例如，对于6b模型，设置max_tokens = 8192，则会报错，因为扣除历史记录和提示词后，模型不能输出那么>多的tokens。
    """
    name: str = 'internlm-chat-20b'
    tokenizer: AutoTokenizer = None
    model: AutoModel = None
    embedding: SentenceTransformer = None

    def __init__(self, pretrained_model_name_or_path: str, embedding_model_path: str, cuda_devices: str = None):
        """
        :param cuda_devices: 运行GPU编号, '0,1'
        """
        # 多GPU环境指定运行在哪个GPU
        DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path=pretrained_model_name_or_path,
                                                       trust_remote_code=True)
        if 'cuda' in DEVICE:  # AMD, NVIDIA GPU can use Half Precision
            if cuda_devices:
                # os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"
                os.environ["CUDA_VISIBLE_DEVICES"] = cuda_devices

            model = AutoModelForCausalLM.from_pretrained(pretrained_model_name_or_path=pretrained_model_name_or_path,
                                                         device_map="balanced",
                                                         torch_dtype=torch.bfloat16,
                                                         trust_remote_code=True)
        else:  # CPU, Intel GPU and other GPU can use Float16 Precision Only
            model = AutoModel.from_pretrained(pretrained_model_name_or_path=pretrained_model_name_or_path,
                                              trust_remote_code=True).float().to(DEVICE).eval()

        self.model = model.eval()
