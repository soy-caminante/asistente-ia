#!/bin/bash

export HF_TOKEN="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"
export VLLM_USE_V1=0

python3 -m vllm.entrypoints.openai.api_server \
  --model microsoft/phi-2 \
  --max-model-len 2048 \
  --dtype float16 \
  --gpu-memory-utilization 0.9 \
  --swap-space 8
