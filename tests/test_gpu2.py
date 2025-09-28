import time
from sentence_transformers import SentenceTransformer
import os

def benchmark():
    sentences = ["This is a test sentence."] * 100  # Batch of 100 sentences

    # CPU
    model_cpu = SentenceTransformer("all-MiniLM-L6-v2")
    start = time.time()
    _ = model_cpu.encode(sentences)
    cpu_time = time.time() - start

    # OpenVINO (if available)
    os.environ["USE_OPENVINO"] = "1"
    model_ov = SentenceTransformer("all-MiniLM-L6-v2")
    start = time.time()
    _ = model_ov.encode(sentences)
    ov_time = time.time() - start

    print(f"CPU time: {cpu_time:.4f} seconds")
    print(f"OpenVINO time: {ov_time:.4f} seconds")
    print(f"Speedup: {cpu_time / ov_time:.2f}x")

benchmark()
