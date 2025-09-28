#!/bin/bash
# AI/setup.sh
set -a && source .env && set +a

# Install dependencies
pip install -r requirements.txt

# Build llama.cpp (if needed)
if [ ! -f llama.cpp/build/bin/llama-run ]; then
    cd llama.cpp
    mkdir -p build && cd build
    cmake .. -DGGML_SYCL=ON -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx -DGGML_SYCL_F16=ON
    cmake --build . -j
fi

