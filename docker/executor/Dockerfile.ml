# ==============================================================================
# Executor ML - Machine Learning / Data Analysis Environment
# ==============================================================================
# Provides a comprehensive environment for data science and ML tasks.
#
# Included packages:
# - numpy, pandas, scipy (data processing)
# - scikit-learn (machine learning)
# - matplotlib, seaborn, plotly (visualization)
# - torch (deep learning - CPU version)
# - transformers, datasets (NLP/Hugging Face)
# - jupyter, ipykernel (notebook support)
# ==============================================================================

FROM python:3.11

LABEL org.opencontainers.image.title="Skills Executor - ML"
LABEL org.opencontainers.image.description="Machine Learning and Data Analysis environment"
LABEL org.opencontainers.image.version="1.0.0"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Install executor server dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install data science packages
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    scipy \
    scikit-learn \
    statsmodels

# Install visualization packages
RUN pip install --no-cache-dir \
    matplotlib \
    seaborn \
    plotly \
    pillow

# Install PyTorch (CPU version for smaller image)
RUN pip install --no-cache-dir \
    torch \
    torchvision \
    --index-url https://download.pytorch.org/whl/cpu

# Install NLP/Transformers packages
RUN pip install --no-cache-dir \
    transformers \
    datasets \
    tokenizers \
    sentencepiece

# Install additional utilities
RUN pip install --no-cache-dir \
    requests \
    httpx \
    pyyaml \
    python-dotenv \
    beautifulsoup4 \
    openpyxl \
    xlrd \
    jupyter \
    ipykernel

# Copy executor server and kernel module
COPY executor_server.py .
COPY ipython_kernel.py .

# Environment
ENV EXECUTOR_NAME=ml
ENV WORKSPACES_DIR=/app/workspaces
ENV PYTHONUNBUFFERED=1

# Create workspaces directory
RUN mkdir -p /app/workspaces

EXPOSE 62681

CMD uvicorn executor_server:app --host 0.0.0.0 --port ${EXECUTOR_PORT:-62681}
