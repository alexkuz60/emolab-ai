#!/usr/bin/env bash
# EmoLab: запуск приложения с GPU.
# essentia-tensorflow ищет CUDA-библиотеки только по LD_LIBRARY_PATH,
# поэтому добавляем пути nvidia/*/lib из .venv до старта интерпретатора.
set -euo pipefail
cd "$(dirname "$0")"

SP=$(.venv/bin/python -c "import site; print(site.getsitepackages()[0])")
NVIDIA_LD=$(ls -d "$SP"/nvidia/*/lib | tr '\n' ':')
export LD_LIBRARY_PATH="${NVIDIA_LD%:}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

exec .venv/bin/python emo_app.py "$@"
