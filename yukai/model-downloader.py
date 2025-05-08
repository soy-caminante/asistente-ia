import pathlib
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name  = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
cache_dir   =  pathlib.Path(__file__).parent /"runtime/cache"

AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
AutoModelForCausalLM.from_pretrained(model_name, cache_dir=cache_dir)