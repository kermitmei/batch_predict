import time
from typing import Optional, Union

import tiktoken
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from transformers import LogitsProcessorList

from llmbase.main.common.dto.req.prompt_batch import PromptBatchDTO
from llmbase.main.common.god import cosmos
from llmbase.main.common.tool.logger import logger
from llmbase.main.llm.chatglm3.model import (EmbeddingRequest, CompletionUsage, ModelCard, ModelList,
                                             ChatCompletionRequest, FunctionCallResponse, ChatMessage,
                                             ChatCompletionResponseChoice, UsageInfo, ChatCompletionResponse,
                                             ChatCompletionResponseStreamChoice, DeltaMessage)
from llmbase.main.llm.chatglm3.utils import process_response, generate_chatglm3, generate_stream_chatglm3

router = APIRouter(prefix="/v1")


class ChatGLM3Service:

    @staticmethod
    def get_embeddings(request: EmbeddingRequest):
        embeddings = [cosmos.llm.embedding.encode(text) for text in request.input]
        embeddings = [embedding.tolist() for embedding in embeddings]

        def num_tokens_from_string(string: str) -> int:
            """
            Returns the number of tokens in a text string.
            use cl100k_base tokenizer
            """
            encoding = tiktoken.get_encoding('cl100k_base')
            num_tokens = len(encoding.encode(string))
            return num_tokens

        response = {
            "data": [
                {
                    "object": "embedding",
                    "embedding": embedding,
                    "index": index
                }
                for index, embedding in enumerate(embeddings)
            ],
            "model": request.model,
            "object": "list",
            "usage": CompletionUsage(
                prompt_tokens=sum(len(text.split()) for text in request.input),
                completion_tokens=0,
                total_tokens=sum(num_tokens_from_string(text) for text in request.input),
            )
        }
        return response

    @staticmethod
    def models():
        model_card = ModelCard(id=cosmos.llm.name)
        return ModelList(data=[model_card])

    @staticmethod
    def create_chat_completion(request: ChatCompletionRequest):
        if len(request.messages) < 1 or request.messages[-1].role == "assistant":
            raise HTTPException(status_code=400, detail="Invalid request")

        gen_params = dict(
            messages=request.messages,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens or 1024,
            echo=False,
            stream=request.stream,
            repetition_penalty=request.repetition_penalty,
            tools=request.tools,
        )
        logger.debug(f"==== request ====\n{gen_params}")

        if request.stream:

            # Use the stream mode to read the first few characters, if it is not a function call, direct stram output
            predict_stream_generator = ChatGLM3Service.predict_stream(request.model, gen_params)
            output = next(predict_stream_generator)
            if not ChatGLM3Service.contains_custom_function(output):
                return EventSourceResponse(predict_stream_generator, media_type="text/event-stream")

            # Obtain the result directly at one time and determine whether tools needs to be called.
            logger.debug(f"First result output：\n{output}")

            function_call = None
            if output and request.tools:
                try:
                    function_call = process_response(output, use_tool=True)
                except:
                    logger.warning("Failed to parse tool call")

            # CallFunction
            if isinstance(function_call, dict):
                function_call = FunctionCallResponse(**function_call)

                """
                In this demo, we did not register any tools.
                You can use the tools that have been implemented in our `tools_using_demo` and implement your own streaming tool implementation here.
                Similar to the following method:
                    function_args = json.loads(function_call.arguments)
                    tool_response = dispatch_tool(tool_name: str, tool_params: dict)
                """
                tool_response = ""

                if not gen_params.get("messages"):
                    gen_params["messages"] = []

                gen_params["messages"].append(ChatMessage(
                    role="assistant",
                    content=output,
                ))
                gen_params["messages"].append(ChatMessage(
                    role="function",
                    name=function_call.name,
                    content=tool_response,
                ))

                # Streaming output of results after function calls
                generate = ChatGLM3Service.predict(request.model, gen_params)
                return EventSourceResponse(generate, media_type="text/event-stream")

            else:
                # Handled to avoid exceptions in the above parsing function process.
                generate = ChatGLM3Service.parse_output_text(request.model, output)
                return EventSourceResponse(generate, media_type="text/event-stream")

        # Here is the handling of stream = False
        response = generate_chatglm3(cosmos.llm.model, cosmos.llm.tokenizer, gen_params)

        # Remove the first newline character
        if response["text"].startswith("\n"):
            response["text"] = response["text"][1:]
        response["text"] = response["text"].strip()

        usage = UsageInfo()
        function_call, finish_reason = None, "stop"
        if request.tools:
            try:
                function_call = process_response(response["text"], use_tool=True)
            except:
                logger.warning(
                    "Failed to parse tool call, maybe the response is not a tool call or have been answered.")

        if isinstance(function_call, dict):
            finish_reason = "function_call"
            function_call = FunctionCallResponse(**function_call)

        message = ChatMessage(
            role="assistant",
            content=response["text"],
            function_call=function_call if isinstance(function_call, FunctionCallResponse) else None,
        )

        logger.debug(f"==== message ====\n{message}")

        choice_data = ChatCompletionResponseChoice(
            index=0,
            message=message,
            finish_reason=finish_reason,
        )
        task_usage = UsageInfo.model_validate(response["usage"])
        for usage_key, usage_value in task_usage.model_dump().items():
            setattr(usage, usage_key, getattr(usage, usage_key) + usage_value)

        return ChatCompletionResponse(
            model=request.model,
            id="",  # for open_source model, id is empty
            choices=[choice_data],
            object="chat.completion",
            usage=usage
        )

    @staticmethod
    def predict(model_id: str, params: dict):
        choice_data = ChatCompletionResponseStreamChoice(
            index=0,
            delta=DeltaMessage(role="assistant"),
            finish_reason=None
        )
        chunk = ChatCompletionResponse(model=model_id, id="", choices=[choice_data], object="chat.completion.chunk")
        yield "{}".format(chunk.model_dump_json(exclude_unset=True))

        previous_text = ""
        for new_response in generate_stream_chatglm3(cosmos.llm.model, cosmos.llm.tokenizer, params):
            decoded_unicode = new_response["text"]
            delta_text = decoded_unicode[len(previous_text):]
            previous_text = decoded_unicode

            finish_reason = new_response["finish_reason"]
            if len(delta_text) == 0 and finish_reason != "function_call":
                continue

            function_call = None
            if finish_reason == "function_call":
                try:
                    function_call = process_response(decoded_unicode, use_tool=True)
                except:
                    logger.warning(
                        "Failed to parse tool call, maybe the response is not a tool call or have been answered.")

            if isinstance(function_call, dict):
                function_call = FunctionCallResponse(**function_call)

            delta = DeltaMessage(
                content=delta_text,
                role="assistant",
                function_call=function_call if isinstance(function_call, FunctionCallResponse) else None,
            )

            choice_data = ChatCompletionResponseStreamChoice(
                index=0,
                delta=delta,
                finish_reason=finish_reason
            )
            chunk = ChatCompletionResponse(
                model=model_id,
                id="",
                choices=[choice_data],
                object="chat.completion.chunk"
            )
            yield "{}".format(chunk.model_dump_json(exclude_unset=True))

        choice_data = ChatCompletionResponseStreamChoice(
            index=0,
            delta=DeltaMessage(),
            finish_reason="stop"
        )
        chunk = ChatCompletionResponse(
            model=model_id,
            id="",
            choices=[choice_data],
            object="chat.completion.chunk"
        )
        yield "{}".format(chunk.model_dump_json(exclude_unset=True))
        yield '[DONE]'

    @staticmethod
    def predict_stream(model_id, gen_params):
        """
        The function call is compatible with stream mode output.

        The first seven characters are determined.
        If not a function call, the stream output is directly generated.
        Otherwise, the complete character content of the function call is returned.

        :param model_id:
        :param gen_params:
        :return:
        """
        output = ""
        is_function_call = False
        has_send_first_chunk = False
        for new_response in generate_stream_chatglm3(cosmos.llm.model, cosmos.llm.tokenizer, gen_params):
            decoded_unicode = new_response["text"]
            delta_text = decoded_unicode[len(output):]
            output = decoded_unicode

            # When it is not a function call and the character length is> 7,
            # try to judge whether it is a function call according to the special function prefix
            if not is_function_call and len(output) > 7:

                # Determine whether a function is called
                is_function_call = ChatGLM3Service.contains_custom_function(output)
                if is_function_call:
                    continue

                # Non-function call, direct stream output
                finish_reason = new_response["finish_reason"]

                # Send an empty string first to avoid truncation by subsequent next() operations.
                if not has_send_first_chunk:
                    message = DeltaMessage(
                        content="",
                        role="assistant",
                        function_call=None,
                    )
                    choice_data = ChatCompletionResponseStreamChoice(
                        index=0,
                        delta=message,
                        finish_reason=finish_reason
                    )
                    chunk = ChatCompletionResponse(
                        model=model_id,
                        id="",
                        choices=[choice_data],
                        created=int(time.time()),
                        object="chat.completion.chunk"
                    )
                    yield "{}".format(chunk.model_dump_json(exclude_unset=True))

                send_msg = delta_text if has_send_first_chunk else output
                has_send_first_chunk = True
                message = DeltaMessage(
                    content=send_msg,
                    role="assistant",
                    function_call=None,
                )
                choice_data = ChatCompletionResponseStreamChoice(
                    index=0,
                    delta=message,
                    finish_reason=finish_reason
                )
                chunk = ChatCompletionResponse(
                    model=model_id,
                    id="",
                    choices=[choice_data],
                    created=int(time.time()),
                    object="chat.completion.chunk"
                )
                yield "{}".format(chunk.model_dump_json(exclude_unset=True))

        if is_function_call:
            yield output
        else:
            yield '[DONE]'

    @staticmethod
    def parse_output_text(model_id: str, value: str):
        """
        Directly output the text content of value

        :param model_id:
        :param value:
        :return:
        """
        choice_data = ChatCompletionResponseStreamChoice(
            index=0,
            delta=DeltaMessage(role="assistant", content=value),
            finish_reason=None
        )
        chunk = ChatCompletionResponse(model=model_id, id="", choices=[choice_data], object="chat.completion.chunk")
        yield "{}".format(chunk.model_dump_json(exclude_unset=True))

        choice_data = ChatCompletionResponseStreamChoice(
            index=0,
            delta=DeltaMessage(),
            finish_reason="stop"
        )
        chunk = ChatCompletionResponse(model=model_id, id="", choices=[choice_data], object="chat.completion.chunk")
        yield "{}".format(chunk.model_dump_json(exclude_unset=True))
        yield '[DONE]'

    @staticmethod
    def contains_custom_function(value: str) -> bool:
        """
        Determine whether 'function_call' according to a special function prefix.

        For example, the functions defined in "tools_using_demo/tool_register.py" are all "get_xxx" and start with "get_"

        [Note] This is not a rigorous judgment method, only for reference.

        :param value:
        :return:
        """
        return value and 'get_' in value

    @staticmethod
    def create_batch_completion(request: ChatCompletionRequest):
        model = cosmos.llm.model
        tokenizer = cosmos.llm.tokenizer
        tokenizer.encode_special_tokens = True

        eos_start = '<|user|>'
        eos_end = '<|assistant|>'
        eos_token_id = [
            tokenizer.eos_token_id,
            tokenizer.get_command(eos_start),
            tokenizer.get_command(eos_end)
        ]
        logger.debug(f"==== messages ====\n{request.messages}")
        prompts = []
        for msg in request.messages:
            prompts.append(eos_start + '\n' + msg.content + '\n' + eos_end)

        gen_kwargs = {
            "max_length": request.max_length or 2048,
            "num_beams": request.num_beams,
            "do_sample": True,
            "top_p": request.top_p,
            "temperature": request.temperature,
            "logits_processor": LogitsProcessorList(),
            "eos_token_id": eos_token_id,
            "repetition_penalty": request.repetition_penalty,
            "tools": request.tools,
        }

        batched_inputs = tokenizer(prompts, return_tensors="pt", padding="longest")
        batched_inputs = batched_inputs.to(model.device)

        batched_outputs = model.generate(**batched_inputs, **gen_kwargs)

        _choices = []
        for input_ids, output_ids in zip(batched_inputs.input_ids, batched_outputs):
            decoded_text = tokenizer.decode(output_ids[len(input_ids):])
            message = ChatMessage(
                role="assistant",
                content=decoded_text.strip(),
                function_call=None
            )

            choice_data = ChatCompletionResponseChoice(
                index=0,
                message=message,
                finish_reason='stop',
            )
            _choices.append(choice_data)

        logger.debug(f"==== choices ====\n{_choices}")

        return ChatCompletionResponse(
            model=request.model,
            id="",  # for open_source model, id is empty
            choices=_choices,
            object="chat.completion",
            usage=None
        )
        

