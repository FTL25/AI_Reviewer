import os
import json
import pdfplumber
from PIL import Image, ImageFont, ImageDraw


def unnormalize_box(bbox, width, height):
    return [
        width * (bbox[0] / 600),
        height * (bbox[1] / 845),
        width * (bbox[2] / 600),
        height * (bbox[3] / 845),
    ]


# Объявление меток
labels = ["B-Header", "I-Header", "B-Affiliation", "I-Affiliation", "B-Text", "I-Text", "B-Author", "I-Author",
          "B-Annotation", "I-Annotation", "B-KeyWords", "I-KeyWords", "B-Reference", "I-Reference", "Other"]
label2id = {"B-Header": 0, "I-Header": 1, "B-Affiliation": 2, "I-Affiliation": 3, "B-Text": 4, "I-Text": 5, "B-Author": 6,
            "I-Author": 7, "B-Annotation": 8, "I-Annotation": 9, "B-KeyWords": 10, "I-KeyWords": 11,
            "B-Reference": 12, "I-Reference": 13, "Other": 14}
id2label = {0: "B-Header", 1: "", 2: "B-Affiliation", 3: "", 4: "B-Text", 5: "", 6: "B-Author", 7: "",
            8: "B-Annotation", 9: "", 10: "B-KeyWords", 11: "", 12: "B-Reference", 13: "",  14: "Other"}
label2color = {0: 'red', 1: 'red', 2: 'purple', 3: 'purple', 4: 'blue', 5: "blue", 6: 'lime', 7: 'lime',
               8: 'cyan', 9: 'cyan', 10: 'green', 11: 'green', 12: "teal", 13: "teal", 14: 'olive'}

if __name__ == "__main__":
    # Подготовка файлов json для обучения
    input_path = r"C:\Users\Asus\Desktop\Предобработка2"
    input_image_path = r"C:\Users\Asus\Desktop\Superfri"
    output_path = r"C:\Users\Asus\Desktop\data2"
    iterator = 0
    for file in os.listdir(input_path):
        document = pdfplumber.open(os.path.join(input_image_path, file))
        with pdfplumber.open(os.path.join(input_path, file)) as pdf:
            IsReference = False
            for page_num, page in enumerate(pdf.pages):
                IsAffiliation = False
                IsAnnotation = False
                IsObject = False
                img = document.pages[page_num].to_image(resolution=150)
                image_path = output_path + r"\images"
                img.save(f"{os.path.join(image_path, file[:-4])}_page_{page_num + 1}.png")
                tokens = []
                bboxes = []
                ner_tags = []
                prev = 0
                prevY = 0
                words = page.extract_words(x_tolerance=3, y_tolerance=3, extra_attrs=["size", "fontname", "y0"])
                for word in words:
                    tokens.append(word["text"])
                    bboxes.append([round(word["x0"]), round(word["top"]), round(word["x1"]), round(word["bottom"])])
                    text = word["text"]
                    font = word["fontname"]
                    size = round(word["size"])
                    currY = word["bottom"] + (abs(word["top"] - word["bottom"]) / 2)
                    if "SFBX" in font or "CIDFont+F1" == font or "CMBX" in font or "CMBXTI" in font or \
                            "SFBI" in font or "OFINBW" in font or "WOQGJA" in font:
                        font += "Bold"
                    if "SFTI" in font or "CIDFont+F2" == font or "CMTI" in font or "CMBXTI" in font or \
                            "SFBI" in font or "Ital" in font:
                        font += "Italic"
                    # Установка меток
                    if text == "References" and "Bold" in font:
                        IsReference = True
                        ner_tags.append(label2id["B-Header"])
                    elif word["bottom"] < 70 or word["y0"] < 50:
                        ner_tags.append(label2id["Other"])
                    elif IsReference:
                        if prev == 7 and word["x0"] > 90:
                            ner_tags.append(label2id["I-Reference"])
                        elif text[0].isdigit() and word["x0"] < 90:
                            ner_tags.append(label2id["B-Reference"])
                            prev = 7
                        elif prev == 6:
                            ner_tags.append(label2id["I-Text"])
                        else:
                            ner_tags.append(label2id["B-Text"])
                            prev = 6
                    elif "Figure" in text and "Bold" in font or "Table" in text and "Bold" in font:
                        IsObject = True
                        ner_tags.append(label2id["B-Header"])
                        prev = 5
                    elif page_num == 0 and (prevY > currY or size < 9):
                        if prev == 1:
                            ner_tags.append(label2id["I-Author"])
                        elif prev == 2:
                            ner_tags.append(label2id["I-Affiliation"])
                        elif prev == 3:
                            ner_tags.append(label2id["I-KeyWords"])
                        elif prev == 4:
                            ner_tags.append(label2id["I-Annotation"])
                        elif prev == 5:
                            ner_tags.append(label2id["I-Header"])
                        else:
                            ner_tags.append(label2id["I-Text"])
                            prev = 6
                    elif size == 9 and page_num == 0 and word["top"] > page.height * 2 / 3:
                        if prev == 3:
                            ner_tags.append(label2id["I-KeyWords"])
                        elif prev == 2:
                            ner_tags.append(label2id["I-Affiliation"])
                        else:
                            ner_tags.append(label2id["B-Affiliation"])
                            prev = 2
                    elif prev == 1 and size == 11:
                        ner_tags.append(label2id["I-Author"])
                    elif "Italic" in font and size == 12 and page_num == 0:
                        if prev == 1:
                            ner_tags.append(label2id["I-Author"])
                        else:
                            ner_tags.append(label2id["B-Author"])
                            prev = 1
                    elif "Bold" in font and size == 11:
                        if "Table" in text or "Figure" in text:
                            IsObject = True
                            ner_tags.append(label2id["B-Header"])
                            prev = 5
                        elif (IsObject and abs(currY - prevY) < 30) or (prev == 5 and abs(prevY - currY) < 10 and IsObject):
                            ner_tags.append(label2id["I-Header"])
                        else:
                            IsObject = False
                            if prev == 6:
                                ner_tags.append(label2id["I-Text"])
                            else:
                                ner_tags.append(label2id["B-Text"])
                                prev = 6
                    elif "Italic" in font and size == 9:
                        if text.startswith("Keywords:"):
                            ner_tags.append(label2id["B-KeyWords"])
                            prev = 3
                        elif prev == 3:
                            ner_tags.append(label2id["I-KeyWords"])
                        elif prev == 4:
                            ner_tags.append(label2id["I-Annotation"])
                        elif prev == 6:
                            ner_tags.append(label2id["I-Text"])
                        else:
                            ner_tags.append(label2id["B-Text"])
                            prev = 6
                    elif size == 9 and page_num == 0:
                        if text.startswith("Keywords:"):
                            ner_tags.append(label2id["B-KeyWords"])
                            prev = 3
                        elif prev == 3:
                            ner_tags.append(label2id["I-KeyWords"])
                        elif prev == 4:
                            ner_tags.append(label2id["I-Annotation"])
                        elif word["x0"] > 95 and abs(prevY - currY) > 10:
                            ner_tags.append(label2id["B-Annotation"])
                            prev = 4
                        elif prev == 6:
                            ner_tags.append(label2id["I-Text"])
                        else:
                            ner_tags.append(label2id["B-Text"])
                            prev = 6
                    elif ("Italic" in font and size == 12) or ("Bold" in font and size == 12) or \
                            ("Bold" in font and size == 14):
                        if prev == 5:
                            ner_tags.append(label2id["I-Header"])
                        else:
                            ner_tags.append(label2id["B-Header"])
                            prev = 5
                    elif size <= 11:
                        if (IsObject and abs(currY - prevY) < 16) or (prev == 5 and abs(prevY - currY) < 10 and IsObject):
                            ner_tags.append(label2id["I-Header"])
                        elif prev == 6:
                            IsObject = False
                            ner_tags.append(label2id["I-Text"])
                        else:
                            IsObject = False
                            ner_tags.append(label2id["B-Text"])
                            prev = 6
                    else:
                        if prev == 1:
                            ner_tags.append(label2id["I-Author"])
                        elif prev == 2:
                            ner_tags.append(label2id["I-Affiliation"])
                        elif prev == 3:
                            ner_tags.append(label2id["I-KeyWords"])
                        elif prev == 4:
                            ner_tags.append(label2id["I-Annotation"])
                        elif prev == 5:
                            ner_tags.append(label2id["I-Header"])
                        else:
                            ner_tags.append(label2id["I-Text"])
                            prev = 6
                    prevY = currY
                check = ",".join(map(str, ner_tags))
                check = check.replace("1,5,1", "1,1,1")
                check = check.replace("0,5,1", "0,1,1")
                ner_tags = [int(N) for N in check.split(",")]

                data = {"id": iterator,
                        "tokens": tokens,
                        "bboxes": bboxes,
                        "ner_tags": ner_tags,
                        "image": f"/content/data/images/{file[:-4]}_page_{page_num + 1}.png"
                        }
                path = output_path + r"\jsons"
                with open(f"{os.path.join(path, file[:-4])}_page_{page_num + 1}.json", 'w',
                          encoding='utf-8') as json_file:
                    json.dump(data, json_file, ensure_ascii=False, indent=4)
                iterator += 1
                image = Image.open(os.path.join(r"C:\Users\Asus\Desktop\data2\images", os.path.basename(data["image"]))).convert(
                    "RGB")
                width, height = image.size
                predictions = data["ner_tags"]
                true_boxes = [unnormalize_box(box, width, height) for box in data["bboxes"]]

                draw = ImageDraw.Draw(image)
                font = ImageFont.truetype("arial.ttf", 13)
                for prediction, box in zip(predictions, true_boxes):
                    draw.rectangle(box, outline=label2color[prediction])
                    draw.text((box[0], box[1] - 20), text=id2label[prediction], fill=label2color[prediction], font=font)
                image.save(os.path.join(r"C:\Users\Asus\Desktop\data_view2", os.path.basename(data["image"])))
        document.close()

