# Chatbot Toan tieu hoc NCKH

Project chuyen tu notebook `nckh-math.ipynb` thanh ung dung Python chay local tren Windows va Linux.
Chatbot giu ba che do su pham, context nhieu luot, bo loc `<think>` va tham so sinh cua notebook:
`enable_thinking=False`, `temperature=0.25`, `top_p=0.85`, `repetition_penalty=1.15`.

## Cau truc

- `app/`: cau hinh, prompt, nap model, suy luan va benchmark.
- `ui/streamlit_app.py`: giao dien web Streamlit.
- `scripts/chat_cli.py`: chat tren terminal.
- `scripts/run_benchmark.py`: chay dung bon bai benchmark Lop 2-5.
- `models/`: dat LoRA checkpoint tai `models/checkpoint-30` va base model Qwen3 8B tai `models/Qwen3-8B-unsloth-bnb-4bit`.

Thu muc `unsloth_compiled_cache/` khong duoc dua vao project va da duoc loai khoi `.gitignore`.

## Cai dat

Yeu cau Python 3.10 tro len.

```bash
cd nckh-math-chatbot
python -m venv .venv
# Windows PowerShell
.\\.venv\\Scripts\\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` dung PyTorch mac dinh. Voi CUDA, cai wheel PyTorch dung phien ban CUDA cua may theo huong dan chinh thuc cua PyTorch. Voi CPU, dat `DEVICE=cpu` va `LOAD_IN_4BIT=false`.

Unsloth la tuy chon. Tren moi truong Linux/CUDA tuong thich, co the cai them `pip install -r requirements-unsloth.txt`; neu Unsloth khong co hoac khong nap duoc, ung dung tu fallback sang Transformers + PEFT.

## Model tu Kaggle

Checkpoint fine-tune cua notebook la LoRA adapter `checkpoint-30`, khong phai thu muc `unsloth_compiled_cache`. Cache chi chua ma Python bien dich, khong co trong so model va khong can sua.

Tai output Kaggle vao thu muc `models`:

```bash
kaggle kernels output aegold/nckh-math -p ./models
```

Neu dung KaggleHub de tai model Kaggle:

```bash
python -m pip install kagglehub
python -c "import kagglehub; print(kagglehub.model_download('aegold/math-nckh', output_dir='./models/checkpoint-30-kaggle'))"
```

Neu output tao thu muc long nhau, dat thu muc chua `adapter_config.json` va/hoac cac file model tai `models/checkpoint-30`. Co the dung duong dan khac bang bien moi truong `MODEL_PATH` hoac tham so `--model`.

```powershell
$env:MODEL_PATH = ".\\models\\checkpoint-30"
$env:BASE_MODEL_PATH = ".\\models\\Qwen3-8B-unsloth-bnb-4bit"
```

Khong commit checkpoint model vao Git. Sao chep `.env.example` thanh `.env` neu muon quan ly bien moi truong rieng; ung dung tu dong doc file nay.

## Chay Streamlit

```bash
streamlit run ui/streamlit_app.py
```

Chon mot trong ba che do. Doi che do hoac bam `Lam moi hoi thoai` se tao session moi; cac luot chat trong session hien tai duoc giu de model hieu cau tra loi tiep theo.

## Chat CLI

```bash
python scripts/chat_cli.py --model ./models/checkpoint-30 --mode socratic
```

Lenh trong CLI:

- `/reset`: lam moi context voi mode hien tai.
- `/mode 1`, `/mode 2`, `/mode 3`: doi mode va tu lam moi context.
- `/quit`: thoat.

Vi du hoi thoai Socratic:

```text
Em: Em khong biet lam bai nay: Tim x, biet: x * 3 - 4 = 11
Gia su AI: ... nhom x * 3 dang giu vai tro gi trong phep tru?
Em: Trong phep tru thi x * 3 la so bi tru dung khong a?
Gia su AI: ...
```

## Benchmark va test

```bash
python scripts/run_benchmark.py --model ./models/checkpoint-30
# Chay them bai Lop 1, thanh bo Lop 1-5
python scripts/run_benchmark.py --model ./models/checkpoint-30 --all-grades --output ./benchmark_results/local_benchmark.md
pytest
```

Benchmark tai hien bon de trong Cell 5: Lop 2 tim thanh phan chua biet, Lop 3 tim thua so chua biet, Lop 4 bai toan Tong-Hieu va Lop 5 chuyen dong deu. Bao cao mac dinh nam tai `benchmark_results/benchmark.md`.

## Cau hinh

Gia tri mac dinh nam trong `config.yaml`: adapter `./models/checkpoint-30`, base model `./models/Qwen3-8B-unsloth-bnb-4bit`, context 4096 va tu chon CUDA/CPU. Co the ghi de bang `MODEL_PATH`, `BASE_MODEL_PATH`, `MAX_SEQ_LEN`, `LOAD_IN_4BIT`, `DEVICE` va `LOG_LEVEL`.
