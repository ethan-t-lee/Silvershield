import json
from pathlib import Path

from deep_translator import GoogleTranslator

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "survey_config.json"
OUTPUT_PATH = ROOT / "survey_translations.json"


def collect_strings(value, out):
    if isinstance(value, str):
        text = value.strip()
        if text:
            out.add(text)
        return
    if isinstance(value, list):
        for item in value:
            collect_strings(item, out)
        return
    if isinstance(value, dict):
        for item in value.values():
            collect_strings(item, out)


def translate_batch(strings, target):
    translator = GoogleTranslator(source="en", target=target)
    translated = translator.translate_batch(strings)
    if not isinstance(translated, list):
        translated = [translated]
    return [text if not isinstance(text, str) or not text else text for text in translated]


def main():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    all_strings = set()
    collect_strings(config.get("consent", {}), all_strings)
    collect_strings(config.get("preTrainingSurvey", {}), all_strings)
    collect_strings(config.get("postTrainingSurvey", {}), all_strings)

    ordered_strings = sorted(all_strings)

    language_targets = {
        "es": "es",
        "zh": "zh-CN",
    }

    output = {"es": {}, "zh": {}}
    batch_size = 30

    for lang, target in language_targets.items():
        for i in range(0, len(ordered_strings), batch_size):
            chunk = ordered_strings[i:i + batch_size]
            try:
                translated_chunk = translate_batch(chunk, target)
            except Exception:
                translated_chunk = chunk

            for src, translated in zip(chunk, translated_chunk):
                output[lang][src] = translated or src

    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Generated {OUTPUT_PATH} with {len(ordered_strings)} source strings")


if __name__ == "__main__":
    main()
