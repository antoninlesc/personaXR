# Setting up RunPod and Running the pipeline



### Tailscale
Instalation : curl -fsSL https://tailscale.com/install.sh | sh
```shell
1. tailscale up

2. tailscale serve --http 80 127.0.0.1:8080
```

From the second command, you will get an URL. Use that to communicate between your frontend and backend.

### GitHub repo
Clone the Repo in the /workplace folder as it is the only one that will be saved if you terminate the pod.
```shell
git clone
Create the .env file
```

### Vim (To edit files)
```properties
sudo apt-get update
sudo apt-get install vim
```

### Running vLLM
Doc found on https://huggingface.co/QuantTrio/Qwen3.5-27B-AWQ

```properties
vllm serve \
    QuantTrio/Qwen3.5-27B-AWQ \
    --served-model-name "qwen-3.5-27b" \
    --swap-space 16 \
    --max-num-seqs 32 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.4 \
    --tensor-parallel-size 2 \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder \
    --reasoning-parser qwen3 \
    --speculative-config '{"method":"qwen3_next_mtp","num_speculative_tokens":2}' \
    --trust-remote-code \
    --host 0.0.0.0 \
    --port 8000
```

1. Tell Hugging Face to download the model files to your persistent storage
mkdir -p /workspace/huggingface_cache
export HF_HOME=/workspace/huggingface_cache

2. Optimize CPU threads
export OMP_NUM_THREADS=4