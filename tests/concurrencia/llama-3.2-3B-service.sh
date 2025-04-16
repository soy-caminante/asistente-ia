#!/bin/bash

export HF_TOKEN="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"

python3 -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.2-3B-Instruct \
  --gpu-memory-utilization 0.9 \
  --max-model-len 6144