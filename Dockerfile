FROM python:3.13-slim

# Instala Rust
RUN apt-get update && apt-get install -y curl
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Instala dependencias de sistema necesarias
RUN apt-get install -y build-essential

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
