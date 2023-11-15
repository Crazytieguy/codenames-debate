import torch
import typer
from accelerate import Accelerator
from peft import PeftModel  # type: ignore
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from trl import is_xpu_available

from .models import generate_game


def main():
    quantization_config = BitsAndBytesConfig(load_in_8bit=True)
    device_map = (
        {"": f"xpu:{Accelerator().local_process_index}"}
        if is_xpu_available()
        else {"": Accelerator().local_process_index}
    )

    peft_model_id = "./llama-7b-hint-giving"
    model = AutoModelForCausalLM.from_pretrained(
        "meta-llama/Llama-2-7b-hf",
        quantization_config=quantization_config,
        device_map=device_map,
        torch_dtype=torch.bfloat16,
    )
    model = PeftModel.from_pretrained(model, peft_model_id)

    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")

    games = [generate_game() for _ in range(10)]
    for game in games:
        prompt = f"{game}\n\nClue:"
        input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(model.device)
        outputs = model.generate(input_ids=input_ids, max_new_tokens=10)
        output_text = tokenizer.batch_decode(
            outputs.detach().cpu().numpy(),  # type: ignore
            skip_special_tokens=True,
        )[0]
        print(output_text, end="\n\n")


if __name__ == "__main__":
    typer.run(main)
