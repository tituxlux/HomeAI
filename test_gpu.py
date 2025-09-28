import time
import intel_extension_for_pytorch as ipex
import torch


import numpy as np
from sentence_transformers import SentenceTransformer
from openvino.runtime import Core
from openvino.frontend import frontend  # Updated import for OpenVINO 2025

def test_openvino_npu():
    # Initialize OpenVINO
    core = Core()
    devices = core.available_devices
    print(f"OpenVINO available devices: {devices}")

    # Set device to NPU if available, otherwise GPU or CPU
    device = "NPU" if "NPU" in devices else "GPU" if "GPU" in devices else "CPU"
    print(f"Using OpenVINO device: {device}")

    # Load SentenceTransformer model
    model = SentenceTransformer("all-MiniLM-L6-v2")
    model.eval()

    # Example input
    example_input = ["This is a test sentence."]
    embeddings_cpu = model.encode(example_input)
    print(f"CPU embeddings shape: {embeddings_cpu.shape}")

    # Export to OpenVINO using the updated API
    try:
        # Get the underlying AutoModel
        pt_model = model[0].auto_model
        pt_model.eval()

        # Example input for tracing
        example_input = {
            "input_ids": torch.randint(0, 100, (1, 16)),  # Example input_ids
            "attention_mask": torch.ones((1, 16)),       # Example attention_mask
            "token_type_ids": torch.zeros((1, 16)),      # Example token_type_ids
        }

        # Convert to OpenVINO IR
        ov_model = frontend.pytorch_to_ov(
            pt_model,
            input=example_input,
            output=torch.randn(1, 384),  # Example output shape
        )

        # Compile for the target device
        compiled_model = core.compile_model(ov_model, device)

        # Run inference
        start_time = time.time()
        ov_embeddings = compiled_model(example_input)[0]
        end_time = time.time()

        print(f"OpenVINO inference on {device}: {end_time - start_time:.4f} seconds")
        print(f"OpenVINO embeddings shape: {ov_embeddings.shape}")

    except Exception as e:
        print(f"Error during OpenVINO conversion: {e}")
        print("Falling back to CPU inference.")
        
def test_pytorch():
    # Print PyTorch version and device info
    
    print(f"PyTorch version: {torch.__version__}")
    print(f"Intel Extension for PyTorch version: {ipex.__version__}")

    # Check available devices
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"Intel XPU (GPU/NPU) available: {torch.xpu.is_available()}")

    # Set device
    device = "xpu" if torch.xpu.is_available() else "cpu"
    print(f"Using device: {device}")

    # Create a random tensor
    x = torch.randn(1000, 1000, device=device)
    y = torch.randn(1000, 1000, device=device)

    # Perform a matrix multiplication
    start_time = time.time()
    z = torch.matmul(x, y)
    end_time = time.time()

    print(f"Matrix multiplication on {device}: {end_time - start_time:.4f} seconds")
    print(f"Result shape: {z.shape}")

    # Check if Intel optimizations are applied
    if device == "xpu":
        print("✅ Intel GPU/NPU (XPU) is working!")
    else:
        print("ℹ️ Using CPU (Intel optimizations may still apply)")

    # Test inference with a small model
    model = torch.nn.Linear(1000, 10).to(device)
    input_data = torch.randn(1, 1000, device=device)
    output = model(input_data)
    print(f"Model inference on {device}: {output.shape}")

if __name__ == "__main__":
    print(f"XPU available: {torch.xpu.is_available()}")
    if torch.xpu.is_available():
        print(f"XPU device name: {torch.xpu.get_device_name(0)}")
    
    # test_pytorch()
    test_openvino_npu()
