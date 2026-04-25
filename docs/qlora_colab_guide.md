# Hướng dẫn chuẩn bị và chạy QLoRA trên Google Colab

## 1. Chạy convert dataset ở local

Từ thư mục root của project:

```powershell
python scripts/convert_dataset_for_sft.py
```

Script sẽ tạo:

- `datasets/sft_train.jsonl`
- `datasets/sft_dev.jsonl`
- `datasets/sft_test.jsonl`

## 2. Zip SFT dataset

Có thể tạo file zip để upload lên Colab:

```powershell
Compress-Archive -Path datasets\sft_train.jsonl,datasets\sft_dev.jsonl,datasets\sft_test.jsonl -DestinationPath sft_dataset.zip -Force
```

Không cần zip dataset gốc 1000 mẫu nếu chỉ train SFT.

## 3. Upload zip lên Colab

Trong Colab:

```python
from google.colab import files
uploaded = files.upload()
```

Sau đó giải nén:

```python
!mkdir -p sft_dataset
!unzip -o sft_dataset.zip -d sft_dataset
```

## 4. Bật GPU runtime

Trong Colab:

1. Vào `Runtime`.
2. Chọn `Change runtime type`.
3. Chọn GPU.
4. Lưu lại và reconnect nếu cần.

Không nên chạy notebook QLoRA trên máy local nếu không có GPU.

## 5. Cài thư viện

Trong notebook Colab:

```python
!pip install -U transformers datasets accelerate peft trl bitsandbytes
```

## 6. Chạy notebook skeleton

Mở hoặc copy nội dung:

```text
notebooks/qlora_debate_trainer_colab.py
```

Chạy lần lượt các section:

- Setup environment
- Upload/load SFT dataset
- Install dependencies
- Check GPU
- Load base model
- Configure QLoRA / LoRA
- Load dataset
- Train SFT
- Save adapter
- Test inference
- Download adapter

Model mặc định:

```python
BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
```

Nếu bị OOM, giảm:

- `MAX_SEQ_LENGTH`
- `per_device_train_batch_size`
- `LORA_RANK`

## 7. Save adapter

Sau khi train, lưu adapter:

```python
trainer.model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
```

Sau đó zip và tải về:

```python
import shutil
from google.colab import files

shutil.make_archive(OUTPUT_DIR, "zip", OUTPUT_DIR)
files.download(f"{OUTPUT_DIR}.zip")
```

## 8. Đưa adapter về project

Giải nén adapter vào:

```text
adapters/
```

Ví dụ:

```text
adapters/ai_debate_trainer_qlora_adapter/
```

Không commit adapter lớn lên GitHub. Project đã ignore nội dung trong `adapters/` và chỉ giữ `.gitkeep`.

## 9. Lưu ý báo cáo đồ án

Khi mô tả dataset, nên nói rõ đây là synthetic template-generated dataset, dùng để prototype pipeline và fine-tuning thử nghiệm. Cần review thủ công một phần trước khi xem là dữ liệu chất lượng cao.
