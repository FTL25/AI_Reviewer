import json
import os
from PIL import Image, ImageFont, ImageDraw


def unnormalize_box(bbox, width, height):
    return [
        width * (bbox[0] / 600),
        height * (bbox[1] / 845),
        width * (bbox[2] / 600),
        height * (bbox[3] / 845),
    ]


input_path = r"C:\Users\Asus\Desktop\data2\jsons"
output_path = r"C:\Users\Asus\Desktop\data_view2"
id2label = {0: "B-Header", 1: "", 2: "B-Affiliation", 3: "", 4: "B-Text", 5: "", 6: "B-Author", 7: "",
            8: "B-Annotation", 9: "", 10: "B-KeyWords", 11: "", 12: "B-Reference", 13: "",  14: "Other"}
label2color = {0: 'red', 1: 'red', 2: 'purple', 3: 'purple', 4: 'blue', 5: "blue", 6: 'lime', 7: 'lime',
               8: 'cyan', 9: 'cyan', 10: 'green', 11: 'green', 12: "teal", 13: "teal", 14: 'olive'}
for file in os.listdir(input_path):
    with open(os.path.join(input_path, file), 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
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
    image.save(os.path.join(output_path, os.path.basename(data["image"])))
