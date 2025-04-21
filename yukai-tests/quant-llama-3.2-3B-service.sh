#!/bin/bash

export HF_TOKEN="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"

python -m vllm.entrypoints.openai.api_server \
  --model neuralmagic/Llama-3.2-3B-Instruct-quantized.w8a8 \
  --port 8000 \
  --max-num-seqs 35 \
  --dtype auto \
  --gpu-memory-utilization 0.9 \
  --max-model-len 16000
