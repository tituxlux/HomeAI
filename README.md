
# Home AI

Home based AI with support for local insertion in a GAR

## Web UI

The first Flask UI lives in `home_ai/` and borrows the VDL chat dashboard layout without tenants or OIDC.

```bash
.venv/bin/flask --app home_ai.wsgi run --host 0.0.0.0 --port 5005
```

Then open `http://localhost:5005` and log in with:

- user: `admin`
- password: `admin`

For a non-default password, set `HOME_AI_ADMIN_PASSWORD` or `HOME_AI_ADMIN_PASSWORD_HASH`.


## Using llama.cpp

'''bash
# Install llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

cmake -B build
cmake --build build --config Release


https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/SYCL.md

make -j
# Download a GGUF Model
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf
# Run with Intel GPU
./main -m mistral-7b-instruct-v0.1.Q4_K_M.gguf -ngl 32 --numa split

# -ngl 32: Offload layers to GPU.
# Monitor GPU usage with sudo intel_gpu_top.

'''
