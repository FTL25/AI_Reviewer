import json
from transformers import LayoutLMv3ForTokenClassification, LayoutLMv3Processor
import pytesseract
from preprocessor import label2id, id2label, label2color
from pdf2image import convert_from_path
import torch
from PIL import ImageDraw, ImageFont
from collections import Counter


def unnormalize_box(bbox, width, height):
    return [
        width * (bbox[0] / 1000),
        height * (bbox[1] / 1000),
        width * (bbox[2] / 1000),
        height * (bbox[3] / 1000),
    ]


def recognition(input_path, output_path):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # Путь к tesseract
    processor = LayoutLMv3Processor.from_pretrained("microsoft/layoutlmv3-base", apply_ocr=True)
    model = LayoutLMv3ForTokenClassification.from_pretrained("./NNModel")
    poppler_path = r"C:\Program Files (x86)\poppler-25.12.0\Library\bin" # Путь к poppler
    images = convert_from_path(input_path, poppler_path=poppler_path, hide_annotations=True)
    output_images = []
    page_num = 1
    pages = []
    IsReference = False
    for image in images:
        texts = {"tokens": [], "classes": [], "boxes": []}
        encoding = processor(image, return_tensors="pt", truncation=True,
                             padding="max_length", stride=128, max_length=512,
                             return_overflowing_tokens=True, return_offsets_mapping=True)
        encoding.pop("overflow_to_sample_mapping")
        encoding.pop("offset_mapping")

        input_ids = encoding['input_ids'][encoding['attention_mask'] == 1]

        true_texts = processor.tokenizer.decode(input_ids).split(" ")
        true_texts[0] = " "
        true_texts[-1] = true_texts[-1][:-4]

        inputs = [{k: v[i].unsqueeze(0) for k, v in encoding.items()} for i in range(0, len(encoding.encodings))]
        logs = []

        for input in inputs:
            with torch.no_grad():
                output = model(**input).logits
                logs.append(output)
        logits = torch.cat(logs, dim=1)
        predictions = torch.softmax(logits, dim=-1)
        predictions = predictions.argmax(-1).squeeze().tolist()
        token_boxes = encoding.bbox.squeeze().tolist()
        if len(token_boxes) < 10:
            token_boxes = sum(token_boxes, [])
        width, height = image.size
        true_predictions = []
        true_boxes = []

        bboxes = [unnormalize_box(box, width, height) for box in token_boxes]

        for prediction, box in zip(predictions, bboxes):
            if box not in true_boxes:
                true_predictions.append(prediction)
                true_boxes.append(box)

        if len(true_texts) > len(true_boxes):
            extra = len(true_texts) - len(true_boxes)
            for i, word in enumerate(true_texts):
                if "</s><s>" in word:
                    ind = i
                    break
            true_texts[ind] = true_texts[ind][:-7]
            true_texts = true_texts[:ind + 1] + true_texts[ind + 1 + extra:]

        if IsReference:
            for j in range(0, len(true_predictions)):
                if true_predictions[j] < 12:
                    true_predictions[j] = 13
        elif "References" in true_texts:
            IsReference = True
            for j in range(true_texts.index("References") + 1, len(true_texts)):
                if true_predictions[j] < 12:
                    true_predictions[j] = 13

        if page_num == 1:
            prevY = 0
            lines = []
            for i, box in enumerate(true_boxes):
                currY = box[1]
                if abs(currY - prevY) > 10:
                    lines.append(i)
                prevY = currY
            lines.append(len(true_boxes) - 1)
            for i in range(0, len(lines) - 1):
                predictions_line = true_predictions[lines[i]:lines[i + 1]]
                if len(predictions_line) < 2:
                    continue
                freq_class = Counter(predictions_line).most_common(1)[0][0]
                if freq_class != label2id["I-Header"] or freq_class != label2id["I-Text"]:
                    true_predictions[lines[i]:lines[i + 1]] = \
                        [label if label == freq_class - 1 else freq_class for label in
                         true_predictions[lines[i]:lines[i + 1]]]

        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("arial.ttf", 13)
        for text, prediction, box in zip(true_texts, true_predictions, true_boxes):
            draw.rectangle(box, outline=label2color[prediction])
            draw.text((box[0], box[1] - 20), text=id2label[prediction], fill=label2color[prediction], font=font)

        output_images.append(image)
        page_num += 1
        texts["tokens"] = true_texts
        texts["classes"] = true_predictions
        texts["boxes"] = true_boxes
        pages.append(texts)
    output_images[0].save(output_path, save_all=True, append_images=output_images[1:])
    return pages, width


id2class = {0: "Header", 1: "Header", 2: "Affiliation", 3: "Affiliation", 4: "Text", 5: "Text", 6: "Author", 7: "Author",
            8: "Annotation", 9: "Annotation", 10: "KeyWords", 11: "KeyWords", 12: "Reference", 13: "Reference", 14: "Other"}
