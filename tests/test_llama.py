from llama_cpp import Llama

llm = Llama(
    model_path="models/mistral-7b-instruct-v0.1.Q4_K_M.gguf",
    n_gpu_layers=32,
    n_ctx=4096,
    chat_format="mistral-instruct",  # Critical for correct behavior
)

output = llm.create_chat_completion(
    messages=[{"role": "user", "content": "Why is the sky blue?"}]
)
print(output["choices"][0]["message"]["content"])
