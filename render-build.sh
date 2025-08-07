#!/usr/bin/env bash
set -e

# Instala Rust en el HOME del usuario
export CARGO_HOME="$HOME/.cargo"
export RUSTUP_HOME="$HOME/.rustup"

if ! command -v cargo &> /dev/null
then
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi

export PATH="$CARGO_HOME/bin:$PATH"

# Instala dependencias del sistema necesarias
apt-get update && apt-get install -y build-essential

# Instala requirements de Python
pip install --upgrade pip
pip install -r requirements.txt
