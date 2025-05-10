#!/bin/bash

export HF_TOKEN="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"

python3 -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --tokenizer meta-llama/Llama-3.1-8B-Instruct \
  --max-model-len 4096 \
  --dtype float32 \
  --port 8000
