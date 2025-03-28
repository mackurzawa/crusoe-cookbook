import os

import torch
from config import Config
from data_processing.processor import Processor
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from trl import SFTTrainer


def initialize_tokenizer(model_id: str, token: str) -> AutoTokenizer:
    """
    Initialize and configure a tokenizer for the specified model.

    Args:
        model_id: The identifier of the pretrained model to load.
        token: The Hugging Face authentication token for accessing the model.

    Returns:
        The configured tokenizer with padding side set to left,
        EOS and BOS tokens added, and pad token set to EOS token.
    """
    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        padding_side="left",
        add_eos_token=True,
        add_bos_token=True,
        token=token
    )
    tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def initialize_model(model_id: str, token: str) -> AutoModelForCausalLM:
    """
    Initialize a quantized causal language model with the specified configuration.

    Args:
        model_id: The identifier of the pretrained model to load.
        token: The Hugging Face authentication token for accessing the model.

    Returns:
        The quantized model configured with 4-bit quantization,
        loaded onto the appropriate CUDA device.
    """
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )

    return AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        trust_remote_code=True,
        use_cache=False,
        token=token,
        device_map={"": "cuda:" + str(int(os.environ.get("LOCAL_RANK") or 0))}
    )


def main() -> None:
    """
    Main function to execute the model training pipeline.
    """
    config = Config()

    model = initialize_model(config.model_id, config.hf_token)
    tokenizer = initialize_tokenizer(config.model_id, config.hf_token)

    processor = Processor(tokenizer=tokenizer)
    dataset = load_dataset(config.dataset_name, config.dataset_config,
                          token=config.hf_token, trust_remote_code=True)
    processed_dataset = processor.process_dataset(dataset, tokenize=True)

    training_args = TrainingArguments(
        output_dir=config.output_dir,
        optim=config.training_args["optim"],
        bf16=True,
        max_grad_norm=config.training_args["max_grad_norm"],
        num_train_epochs=2,
        warmup_ratio=config.training_args["warmup_ratio"],
        group_by_length=True,
        gradient_checkpointing=True,
        ddp_find_unused_parameters=False,
        warmup_steps=2,
        per_device_train_batch_size=config.training_args["per_device_train_batch_size"],
        gradient_accumulation_steps=config.training_args["gradient_accumulation_steps"],
        learning_rate=config.training_args["learning_rate"],
        logging_steps=config.training_args["logging_steps"],
        save_strategy="steps",
        save_steps=100,
        evaluation_strategy="steps",
        eval_steps=50,
        do_eval=True,
        report_to=None,
    )

    peft_config = LoraConfig(
        r=32,
        lora_alpha=64,
        target_modules=config.lora_target_modules,
        bias="none",
        lora_dropout=0.05,
        task_type="CAUSAL_LM",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=processed_dataset["train"],
        eval_dataset=processed_dataset["validation"],
        peft_config=peft_config,
        args=training_args,
    )
    trainer.train()


if __name__ == "__main__":
    main()