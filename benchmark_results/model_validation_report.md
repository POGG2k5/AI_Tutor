# Bao cao kiem thu chatbot Toan

## Trang thai test local

**Chua the chay inference local.** Tai thoi diem kiem tra:

- `models/checkpoint-30` chua ton tai.
- May chua co `torch`, `transformers`, `peft` va `streamlit`.
- Lenh `kaggle kernels output aegold/nckh-math` chi lay artifact dau ra cua kernel, khong lay dataset model duoc mount tai `/kaggle/input/models/...`.
- Lenh Kaggle vua thu chi tai `unsloth_compiled_cache` va `nckh-math.log`; cac file cache da duoc xoa khoi `models/`.

Vi vay, cac ket qua ben duoi la ket qua model da chay tren Kaggle va duoc trich tu `D:/NCKH/nckh-math.log`, khong phai ket qua chay local moi.

## Bang bai toan

| Lop | Bai toan | Dap an dung | Ket qua da co | Danh gia |
|---|---|---:|---|---|
| 1 | Co 7 qua tao, them 5 qua. Hoi co tat ca bao nhieu qua? | 12 qua | Chua chay | Chua danh gia |
| 2 | Tim x, biet: x + 18 = 45 | x = 27 | Model hoi vai tro cua x | Dung huong Socratic, chua tinh dap an |
| 3 | Tim x, biet: x * 4 = 36 | x = 9 | Model hoi x dang lam gi | Chua dat: cau hoi con mo ho, thieu so 4 va 36 |
| 4 | Tong 24 cai keo, An nhieu hon Binh 6 cai | An 15, Binh 9 | Model goi y dat bien | Chua dat: dung tu cam `phuong trinh`, chua theo cach tieu hoc cu the |
| 5 | 120 km trong 2 gio 30 phut | 48 km/gio | Model hoi vai tro cua van toc | Dung huong ban dau, nhung cau hoi chua gan du lieu 120 va 2 gio 30 phut |

## Ket qua multi-turn da co

Model da duoc nap thanh cong tren Kaggle bang Unsloth voi checkpoint-30, LoRA adapter va 2 GPU Tesla T4.

Hoi thoai da kiem tra:

```text
Em: Tinh x, biet x * 3 - 4 = 11
Model: Xac dinh nhom chua biet trong x * 3 - 4 = 11.

Em: x * 3 la so bi tru dung khong?
Model: Xac nhan x * 3 la so bi tru va hoi tiep ve so tru, hieu.

Em: x * 3 = 15, tim x the nao?
Model: Goi y phep chia 15 cho 3, khong noi dap so cuoi cung.
```

Danh gia: model giu duoc context 3 luot va dan hoc sinh den phep chia 15 cho 3. Tuy nhien, log cu cho thay mot so cau hoi con vague va bai Lop 4 con sinh tu cam `phuong trinh`; can benchmark lai sau khi nap model local.

## Ket luan

Model **da tung chay thanh cong tren Kaggle**, nhung chua the ket luan ban local chay OK cho den khi co checkpoint trong `models/checkpoint-30`.

Sau khi dat checkpoint vao dung thu muc, chay:

```powershell
cd D:\NCKH\nckh-math-chatbot
python -m pip install -r requirements.txt
python scripts/run_benchmark.py --model .\models\checkpoint-30 --output .\benchmark_results\local_benchmark.md
```

Bao cao `local_benchmark.md` se la ket qua inference that cua 4 bai Lop 2-5. Them bai Lop 1 vao `app/benchmark.py` neu muon benchmark day du Lop 1-5.
