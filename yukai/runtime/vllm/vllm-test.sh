#!/bin/bash

export HF_TOKEN="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"

python3 -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --tokenizer meta-llama/Llama-3.1-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096 \
  --quantization bitsandbytes \
  --port 8081
