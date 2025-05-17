FROM python:3.12-slim

# Install curl and unzip to fetch and install uv
RUN apt-get update && apt-get install -y curl unzip && \
    curl -LsSf https://astral.sh/uv/install.sh | sh

# Set the PATH to include uv
ENV PATH="/root/.local/bin:$PATH"

# Set the working directory
WORKDIR /app

# Copy only the dependency files to leverage Docker cache
COPY pyproject.toml .

# Install dependencies using uv into the system environment
RUN uv pip install --system fastapi uvicorn python-multipart python-magic

RUN apt-get update && apt-get install -y git curl unzip && \
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
# Copy the rest of your application code
COPY . .

# Expose the port your FastAPI app runs on
EXPOSE 8080

# Command to run your FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]