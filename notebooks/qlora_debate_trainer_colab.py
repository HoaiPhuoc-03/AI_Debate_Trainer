"""
AI Debate Trainer QLoRA Colab Skeleton

Use this file as a guide for Google Colab or Kaggle. Do not run this locally
unless you have a CUDA GPU and enough VRAM. This project phase only prepares
the notebook skeleton; it does not train on the local machine.

If you hit OOM, reduce max_seq_length, per_device_train_batch_size, or LORA_RANK.
"""


# 1. Setup environment

BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
OUTPUT_DIR = "ai_debate_trainer_qlora_adapter"
DATA_DIR = "sft_dataset"
MAX_SEQ_LENGTH = 1024
LORA_RANK = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05


# 2. Upload/load SFT dataset

# In Colab, upload a zip that contains:
# - sft_train.jsonl
# - sft_dev.jsonl
# - sft_test.jsonl
#
# Example Colab cells:
# from google.colab import files
# uploaded = files.upload()
# !mkdir -p sft_dataset
# !unzip -o sft_dataset.zip -d sft_dataset


# 3. Install dependencies

# Run in Colab, not locally:
# !pip install -U transformers datasets accelerate peft trl bitsandbytes


# 4. Check GPU

# import torch
# print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU")
# print(torch.cuda.get_device_properties(0).total_memory / 1024**3 if torch.cuda.is_available() else 0, "GB")


# 5. Load base model

# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
#
# tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
# if tokenizer.pad_token is None:
#     tokenizer.pad_token = tokenizer.eos_token
#
# bnb_config = BitsAndBytesConfig(
#     load_in_4bit=True,
#     bnb_4bit_quant_type="nf4",
#     bnb_4bit_compute_dtype=torch.float16,
#     bnb_4bit_use_double_quant=True,
# )
#
# model = AutoModelForCausalLM.from_pretrained(
#     BASE_MODEL,
#     quantization_config=bnb_config,
#     device_map="auto",
#     trust_remote_code=True,
# )


# 6. Configure QLoRA / LoRA

# from peft import LoraConfig
#
# peft_config = LoraConfig(
#     r=LORA_RANK,
#     lora_alpha=LORA_ALPHA,
#     lora_dropout=LORA_DROPOUT,
#     bias="none",
#     task_type="CAUSAL_LM",
#     target_modules=[
#         "q_proj",
#         "k_proj",
#         "v_proj",
#         "o_proj",
#         "gate_proj",
#         "up_proj",
#         "down_proj",
#     ],
# )


# 7. Load dataset

# from datasets import load_dataset
#
# dataset = load_dataset(
#     "json",
#     data_files={
#         "train": f"{DATA_DIR}/sft_train.jsonl",
#         "validation": f"{DATA_DIR}/sft_dev.jsonl",
#         "test": f"{DATA_DIR}/sft_test.jsonl",
#     },
# )
#
# def format_messages(example):
#     text = tokenizer.apply_chat_template(
#         example["messages"],
#         tokenize=False,
#         add_generation_prompt=False,
#     )
#     return {"text": text}
#
# dataset = dataset.map(format_messages)


# 8. Train SFT

# from trl import SFTConfig, SFTTrainer
#
# training_args = SFTConfig(
#     output_dir=OUTPUT_DIR,
#     max_seq_length=MAX_SEQ_LENGTH,
#     per_device_train_batch_size=1,
#     gradient_accumulation_steps=8,
#     learning_rate=2e-4,
#     num_train_epochs=2,
#     logging_steps=10,
#     save_strategy="epoch",
#     eval_strategy="epoch",
#     fp16=True,
#     packing=False,
#     dataset_text_field="text",
# )
#
# trainer = SFTTrainer(
#     model=model,
#     args=training_args,
#     train_dataset=dataset["train"],
#     eval_dataset=dataset["validation"],
#     peft_config=peft_config,
#     tokenizer=tokenizer,
# )
#
# trainer.train()


# 9. Save adapter

# trainer.model.save_pretrained(OUTPUT_DIR)
# tokenizer.save_pretrained(OUTPUT_DIR)


# 10. Test inference

# from peft import PeftModel
#
# test_messages = [
#     {
#         "role": "system",
#         "content": "Bạn là AI Debate Trainer. Luôn phản biện lập luận của người dùng, chấm CER theo Claim-Evidence-Reasoning và đưa feedback cải thiện bằng tiếng Việt. Trả lời đúng format [REBUTTAL], [CER], [FEEDBACK].",
#     },
#     {
#         "role": "user",
#         "content": "Chủ đề: Có nên cấm điện thoại trong lớp học?\nLập trường người dùng: support\nĐộ khó: intermediate\nNhóm tuổi: teen\nTrình độ: basic\nLập luận người dùng: Nên cấm vì điện thoại làm học sinh mất tập trung.",
#     },
# ]
#
# prompt = tokenizer.apply_chat_template(test_messages, tokenize=False, add_generation_prompt=True)
# inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
# output_ids = model.generate(**inputs, max_new_tokens=350, temperature=0.4, do_sample=True)
# print(tokenizer.decode(output_ids[0], skip_special_tokens=True))


# 11. Download adapter

# import shutil
# from google.colab import files
#
# shutil.make_archive(OUTPUT_DIR, "zip", OUTPUT_DIR)
# files.download(f"{OUTPUT_DIR}.zip")
