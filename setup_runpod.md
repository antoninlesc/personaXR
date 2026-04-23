# Setting up RunPod and Running the pipeline
uvicorn app.main:app --host 0.0.0.0 --port 8080


### Tailscale
Instalation : curl -fsSL https://tailscale.com/install.sh | sh
To bypass RunPod, we run in mode "userspace" : tailscaled --tun=userspace-networking --state=/workspace/tailscale.state > /dev/null 2>&1 &

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
This documentation might e depracated as the latest version of vllm support the changes in the nightly version the doc suggests.

So just install the latest version of:
```properties
pip install vllm transformers
```

Enter the virtual environment of personaXR before, 
```properties
source .venv/bin/activate
```
Add those export to the ~/.bashrc file to make the change across all the terminals.

1. Tell Hugging Face to download the model files to your persistent storage
```properties
mkdir -p /workspace/huggingface_cache
export HF_HOME=/workspace/huggingface_cache
```
```properties
mkdir -p /workspace/vllm_cache
export VLLM_CACHE_ROOT=/workspace/vllm_cache
```
2. Optimize CPU threads
```properties
export OMP_NUM_THREADS=4
```
Then you can run this command:
```properties
vllm serve QuantTrio/Qwen3.5-27B-AWQ \
     --served-model-name "qwen-3.5-27b" \
     --max-model-len 8192 \
     --gpu-memory-utilization 0.6 \
     --tensor-parallel-size 2 \
     --trust-remote-code \
     --host 0.0.0.0 \
     --port 8000
```

If you are unsure that the correct environment variables are in the ~/.bashrc file and that they aren't ignore.
Just add them before the vllm command.
```shell
HF_HOME=/workspace/huggingface_cache \
VLLM_CACHE_ROOT=/workspace/vllm_cache \
vllm serve QuantTrio/Qwen3.5-27B-AWQ \
     --served-model-name "qwen-3.5-27b" \
     --max-model-len 8192 \
     --gpu-memory-utilization 0.6 \
     --tensor-parallel-size 2 \
     --trust-remote-code \
     --host 0.0.0.0 \
     --port 8000
```