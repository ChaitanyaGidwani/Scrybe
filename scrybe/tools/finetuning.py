"""Scrybe Fine-Tuning & Distillation Pipeline.

Prepares high-quality datasets for fine-tuning Small Language Models (SLMs)
such as Qwen-2.5-7B-Instruct or Llama-3.1-8B-Instruct on structured DOM extraction:
1. Formats training samples into ChatML (OpenAI/HuggingFace) and Alpaca JSONL formats.
2. Injects adversarial negative samples (non-pricing DOMs, terms pages) to teach the
   model to return empty/null values instead of hallucinating.
3. Generates ready-to-run Unsloth / QLoRA training scripts.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

SYSTEM_EXTRACTION_PROMPT = (
    "You are Scrybe Analyst Agent, an expert in structured competitor web intelligence. "
    "Extract structured competitor product and pricing records strictly from the provided HTML/Markdown. "
    "Rules:\n"
    "1. Never hallucinate. If a pricing value or tier is not explicitly stated in the source, use null.\n"
    "2. If the page does not contain competitor pricing, return an empty pricing_tiers list.\n"
    "3. Output only valid JSON conforming strictly to the CompetitorProductRecord schema."
)

ADVERSARIAL_NEGATIVE_SAMPLES = [
    {
        "input_dom": """
        <div class="terms-page">
            <h1>Terms of Service</h1>
            <p>By accessing our API, you agree not to reverse engineer or abuse our systems.</p>
            <p>For billing inquiries, contact accounting@example.com.</p>
        </div>
        """,
        "target": {
            "company_name": "Example Corp",
            "product_name": "API Service",
            "source_url": "https://example.com/terms",
            "pricing_tiers": [],
            "enterprise_terms_mentioned": True,
            "rate_limits_summary": None,
            "citation_text": "Terms of Service page; no pricing tiers listed.",
        },
    },
    {
        "input_dom": """
        <section class="careers">
            <h2>Join Our AI Engineering Team</h2>
            <p>We are hiring Senior Systems Engineers. Competitive compensation and equity package.</p>
            <span>Remote-first culture across US and Europe.</span>
        </section>
        """,
        "target": {
            "company_name": "AI Startup",
            "product_name": "Careers Page",
            "source_url": "https://aistartup.com/careers",
            "pricing_tiers": [],
            "enterprise_terms_mentioned": False,
            "rate_limits_summary": None,
            "citation_text": "Careers page with zero pricing information.",
        },
    },
]


class FineTuningPipeline:
    """Prepares and exports datasets for fine-tuning extraction SLMs."""

    def __init__(self, system_prompt: str = SYSTEM_EXTRACTION_PROMPT):
        self.system_prompt = system_prompt

    def format_chatml_sample(
        self, 
        dom_content: str, 
        target_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert a (DOM, target) pair into ChatML format for HuggingFace/Unsloth."""
        clean_target = {
            "company_name": target_record.get("company_name", "Unknown"),
            "product_name": target_record.get("product_name", "Standard API"),
            "source_url": target_record.get("source_url", ""),
            "pricing_tiers": target_record.get("pricing_tiers", []),
            "enterprise_terms_mentioned": target_record.get("enterprise_terms_mentioned", False),
            "rate_limits_summary": target_record.get("rate_limits_summary"),
            "citation_text": target_record.get("citation_text", ""),
        }

        return {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": f"Extract structured pricing from the following web DOM excerpt:\n\n```html\n{dom_content.strip()}\n```",
                },
                {
                    "role": "assistant",
                    "content": json.dumps(clean_target, indent=2),
                },
            ]
        }

    def format_alpaca_sample(
        self, 
        dom_content: str, 
        target_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert a (DOM, target) pair into Alpaca instruction format."""
        clean_target = {
            "company_name": target_record.get("company_name", "Unknown"),
            "product_name": target_record.get("product_name", "Standard API"),
            "source_url": target_record.get("source_url", ""),
            "pricing_tiers": target_record.get("pricing_tiers", []),
            "enterprise_terms_mentioned": target_record.get("enterprise_terms_mentioned", False),
            "rate_limits_summary": target_record.get("rate_limits_summary"),
            "citation_text": target_record.get("citation_text", ""),
        }

        return {
            "instruction": self.system_prompt,
            "input": dom_content.strip(),
            "output": json.dumps(clean_target, indent=2),
        }

    def export_dataset(
        self,
        samples: List[Dict[str, Any]],
        output_path: Path,
        format_type: str = "chatml",
        include_negatives: bool = True,
    ) -> int:
        """Export samples to a JSONL file for training.

        Args:
            samples: List of dicts with 'sample_html_snippet' (or 'input_dom') and record fields.
            output_path: File path to save the .jsonl.
            format_type: 'chatml' or 'alpaca'.
            include_negatives: If True, appends adversarial negative samples.

        Returns:
            Total count of exported training samples.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        count = 0

        with open(output_path, "w", encoding="utf-8") as f:
            # 1. Process positive samples
            for s in samples:
                dom = s.get("sample_html_snippet") or s.get("input_dom") or ""
                if not dom:
                    continue

                if format_type == "alpaca":
                    entry = self.format_alpaca_sample(dom, s)
                else:
                    entry = self.format_chatml_sample(dom, s)

                f.write(json.dumps(entry) + "\n")
                count += 1

            # 2. Process adversarial negative samples
            if include_negatives:
                for neg in ADVERSARIAL_NEGATIVE_SAMPLES:
                    dom = neg["input_dom"]
                    target = neg["target"]
                    if format_type == "alpaca":
                        entry = self.format_alpaca_sample(dom, target)
                    else:
                        entry = self.format_chatml_sample(dom, target)

                    f.write(json.dumps(entry) + "\n")
                    count += 1

        return count

    @classmethod
    def generate_unsloth_train_script(
        cls, 
        dataset_path: str = "dataset_chatml.jsonl",
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        output_dir: str = "lora_model",
    ) -> str:
        """Generate a complete, ready-to-run Python script for Unsloth 4-bit QLoRA fine-tuning."""
        return f'''# Auto-generated Unsloth QLoRA Fine-Tuning Script for Scrybe Analyst SLM
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

max_seq_length = 4096
model_name = "{model_name}"

# 1. Load model with 4-bit quantization
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_name,
    max_seq_length=max_seq_length,
    load_in_4bit=True,
)

# 2. Add LoRA adapters targeting linear projections
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)

# 3. Load dataset
dataset = load_dataset("json", data_files="{dataset_path}", split="train")

# 4. Train with SFTTrainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="messages",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    packing=False,
    args=TrainingArguments(
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        warmup_ratio=0.05,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        output_dir="{output_dir}",
        save_strategy="epoch",
        optim="adamw_8bit",
        seed=42,
    ),
)

trainer.train()
model.save_pretrained("{output_dir}_final")
tokenizer.save_pretrained("{output_dir}_final")
print("✅ Fine-tuning complete. Model saved to {output_dir}_final")
'''
