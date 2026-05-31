import json
import re


def get_length(token_num, page):
    prediction = page["classes"][token_num]
    end_num = token_num
    while prediction == page["classes"][end_num] and end_num < len(page["classes"]) - 1:
        end_num += 1
    return end_num - token_num


def get_lines(token_num, page, length):
    lines = []
    str = page["tokens"][token_num]
    prevY = page["boxes"][token_num][1]
    for i in range(token_num + 1, token_num + length):
        currY = page["boxes"][i][1]
        if abs(prevY - currY) > 10:
            lines.append(str)
            str = ""
        str += " " + page["tokens"][i]
        prevY = currY
    lines.append(str)
    return lines


def get_text(token_num, page, length):
    str = page["tokens"][token_num]
    for i in range(token_num + 1, token_num + length):
        str += " " + page["tokens"][i]
    return str


def title_check(words, boxes):
    mistakes = []
    for word in words:
        if word[0].islower() and word not in function_words:
            mistakes.append(f"- слово {word} должно начинаться с заглавной буквы")
    prevX = 0
    prevWord = ""
    for word, box in zip(words, boxes):
        currX = box[0]
        if currX < prevX:
            if prevWord in function_words:
                mistakes.append(f"- завершающий строку предлог (союз) следует перенести на следующую строку")
        prevX = currX
        prevWord = word
    if len(mistakes) == 0:
        mistakes.append("- ошибки не найдены")
    return mistakes


def author_check(text):
    footnote = True
    initials = True
    mistakes = []
    authors = text.split(",")
    for author in authors:
        author = author.strip().split(" ")
        if len(author[-1]) == 1:
            author = author[:-1]
        if author[-1][-1].isalpha():
            footnote = False
        lens = [len(X) for X in author]
        if lens[-1] == min(lens):
            initials = False
    if not footnote:
        mistakes.append("- после фамилии автора должно следовать указание на аффилиацию, оформленную в виде сноски")
    if not initials:
        mistakes.append("- инициалы автора должны располагаться перед фамилией")
    if len(mistakes) == 0:
        mistakes.append("- ошибки не найдены")
    return mistakes


def annotation_check(text):
    mistakes = []
    if " Fig. " in text or " Figure " in text:
        mistakes.append("- аннотация не должна содержать ссылок на рисунки")
    if " Tab. " in text or " Table " in text:
        mistakes.append("- аннотация не должна содержать ссылок на таблицы")
    if re.search(r"\(\d\)", text):
        mistakes.append("- аннотация не должна содержать перекрёстных ссылок")
    if "financial support" in text or "funded" in text or "supported" in text:
        mistakes.append("- аннотация не должна содержать благодарностей")
    text = text.split(" ")
    if len(text) < 150 or len(text) > 250:
        mistakes.append("- оптимальный размер аннотации от 150 до 250 слов")
    dot = False
    for word in text:
        if dot:
            if word[0].islower():
                mistakes.append("- аннотация не должна содержать неопределенных сокращений")
                break
        if word[-1] == ".":
            dot = True
        else:
            dot = False
    if len(mistakes) == 0:
        mistakes.append("- ошибки не найдены")
    return mistakes


def keywords_check(text, prev):
    mistakes = []
    if prev != "Annotation":
        mistakes.append("- список ключевых слов необходимо расположить сразу после аннотации")
    words = text.split(", ")
    if len(words) < 4 or len(words) > 10:
        mistakes.append("- в списке должно быть от 4 до 10 ключевых слов")
    for word in words:
        if word[0].isupper():
            mistakes.append("- все ключевые слова необходимо начинать со строчных букв, кроме имен собственных")
            break
    if len(words) == text.split(","):
        mistakes.append("- ключевые слова в списке должны быть разделены запятыми")
    if len(mistakes) == 0:
        mistakes.append("- ошибки не найдены")
    return mistakes


def affiliation_check(text, lines):
    mistakes = []
    text = text.split(", ")
    if len(text) % 3 != 0:
        mistakes.append("- аффилиация должна содержать организацию, город и страну автора")
    if len(mistakes) == 0:
        mistakes.append("- ошибки не найдены")
    return mistakes


def header_check(text):
    mistakes = []
    if "Introduction" in text and text[0].isdigit():
        mistakes.append("- введение не нумеруется")
    elif "Conclusion" in text and text[0].isdigit():
        mistakes.append("- заключение не нумеруется")
    elif "Acknowledgements" in text or "Acknowledgments" in text and text[0].isdigit():
        mistakes.append("- благодарности не нумеруются")
    elif "References" in text and text[0].isdigit():
        mistakes.append("- заголовок списка литературы не нумеруется")
    if "Introduction" not in text and "Acknowledgements" not in text and "Acknowledgments" not in text and "Conclusion" not in text \
            and "References" not in text:
        if not text[0].isdigit():
            mistakes.append(f"- необходимо нумеровать заголовок {text}")
    for word in text.split(" ")[1:]:
        if word[0].islower() and word not in function_words:
            mistakes.append(f"- в заголовке первая буква слова {word} должна быть заглавной")
    if text[-1] == ".":
        mistakes.append("- в конце заголовков точка не ставится")
    return mistakes


def figure_check(lines, boxes, width):
    mistakes = []
    j = 0
    prevY = boxes[j][1]
    for line in lines:
        a = boxes[j][0]
        currY = boxes[j][1]
        if abs(prevY - currY) > 40:
            break
        j = len(line.split(" ")) - 1
        b = boxes[j][2]
        median = ((a + ((b - a) / 2)) / width)
        if median < 0.485 or median > 0.515:
            mistakes.append(f"- рисунок {lines[0].split(' ')[1][0]} должен иметь выравнивание по центру")
            break
        prevY = currY
        j += 1
    if lines[-1][-1] == ".":
        mistakes.append(f"- в конце названия рисунка {lines[0].split(' ')[1][0]} не должно быть точки")
    return mistakes


def table_check(lines, boxes, width):
    mistakes = []
    j = 0
    prevY = boxes[j][1]
    for line in lines:
        a = boxes[j][0]
        currY = boxes[j][1]
        if abs(prevY - currY) > 15:
            break
        j = len(line.split(" ")) - 1
        b = boxes[j][2]
        median = ((a + ((b - a) / 2)) / width)
        if median < 0.485 or median > 0.515:
            mistakes.append(f"- таблица {lines[0].split(' ')[1][0]} должна иметь выравнивание по центру")
            break
        prevY = currY
        j += 1
    if lines[-1][-1] == ".":
        mistakes.append(f"- в конце названия таблицы {lines[0].split(' ')[1][0]} не должно быть точки.")
    return mistakes


def references_check(text):
    mistakes = []
    words = text.split(" ")
    if "Figure" in text:
        if words[words.index("Figure") - 1][-1] != ".":
            mistakes.append(f"- ссылку на рисунок {re.sub(r'[^0-9]', '', words[words.index('Figure') + 1])} необходимо оформить в виде \"Fig. {re.sub(r'[^0-9]', '', words[words.index('Figure') + 1])}\"")
    if "Fig." in text:
        ind = 0
        for word in words:
            if "Fig." in word:
                break
            ind += 1
        if ind == 0 or words[ind - 1] == ".":
            mistakes.append(f"- ссылку на рисунок {re.sub(r'[^0-9]', '', words[ind + 1])} в начале предложения необходимо оформить в виде \"Figure {re.sub(r'[^0-9]', '', words[ind + 1])}\"")
    if "Table" in text:
        if words[words.index("Table") - 1][-1] != ".":
            mistakes.append(f"- ссылку на таблицу {re.sub(r'[^0-9]', '', words[words.index('Table') + 1])} необходимо оформить в виде \"Tab. {re.sub(r'[^0-9]', '', words[words.index('Table') + 1])}\"")
    if "Tab." in text:
        ind = 0
        for word in words:
            if "Tab." in word:
                break
            ind += 1
        if ind == 0 or words[ind - 1] == ".":
            mistakes.append(f"- ссылку на таблицу {re.sub(r'[^0-9]', '', words[ind + 1])} в начале предложения необходимо оформить в виде \"Table {re.sub(r'[^0-9]', '', words[ind + 1])}\"")
    return mistakes


def validation(pages, width):
    mistakes = [[], [], [], [], [], [], [], []]
    page_num = 1
    references_links = []
    references_len = 0
    layout = [0] * 6
    layout_order = 1
    for page in pages:
        page["classes"] = [id2label[X] for X in page["classes"]]
        token_num = 0
        prev = ""

        text_page = get_text(token_num, page, len(page["tokens"]))
        brackets = re.findall(r"\[[\d\s\-,]+\]", text_page)
        for bracket in brackets:
            bracket = bracket[1:-1]
            if "-" in bracket:
                refs = bracket.split("-")
                references_links.append(range(int(refs[0]), int(refs[1])))
            elif "," in bracket:
                refs = bracket.split(", ")
                for ref in refs:
                    references_links.append(int(ref))
            else:
                references_links.append(int(bracket))
        wrong_brackets = re.findall(r"(\[\d+\], )+\[\d+\]", text_page)
        if len(wrong_brackets) > 0:
            mistakes[6] += [f"- перечисляемые перекрестные ссылки {brackets} следует отделять пробелами и заключить в одни квадратные скобки"]

        while token_num < len(page["tokens"]):
            a = page["tokens"][token_num]
            length = 0
            if page_num == 1:
                if page["classes"][token_num] == "Header":
                    length = get_length(token_num, page)
                    text = get_text(token_num, page, length)
                    if length < 3 and len(mistakes[0]) == 0 or len(text) < 3:
                        token_num += 1
                        continue
                    elif len(mistakes[0]) == 0:
                        if layout[0] == 0:
                            layout[0] = layout_order
                            layout_order += 1
                        words = text.split(" ")
                        mistakes[0] = title_check(words, page["boxes"][token_num:token_num + len(words)])
                    elif "Figure" in text:
                        token_num = page["tokens"][token_num:].index("Figure") + len(page["tokens"][:token_num])
                        length = get_length(token_num, page)
                        mistakes[6] += figure_check(get_lines(token_num, page, length),
                                                    page["boxes"][token_num:token_num + length], width)
                    elif "Table" in text:
                        token_num = page["tokens"][token_num:].index("Table") + len(page["tokens"][:token_num])
                        length = get_length(token_num, page)
                        mistakes[6] += table_check(get_lines(token_num, page, length),
                                                   page["boxes"][token_num:token_num + length], width)
                    elif page["boxes"][token_num][0] < width / 4:
                        mistakes[5] += header_check(text)
                    prev = "Header"
                elif page["classes"][token_num] == "Text":
                    length = get_length(token_num, page)
                    if length > 2:
                        mistakes[6] += references_check(get_text(token_num, page, length))
                    prev = "Text"
                elif page["classes"][token_num] == "Author":
                    length = get_length(token_num, page)
                    if length < 3:
                        token_num += 1
                        continue
                    if len(mistakes[1]) == 0:
                        if layout[1] == 0:
                            layout[1] = layout_order
                            layout_order += 1
                        mistakes[1] = author_check(get_text(token_num, page, length))
                    prev = "Author"
                elif page["classes"][token_num] == "Annotation":
                    length = get_length(token_num, page)
                    if length < 3:
                        token_num += 1
                        continue
                    if len(mistakes[2]) == 0:
                        if layout[2] == 0:
                            layout[2] = layout_order
                            layout_order += 1
                        mistakes[2] = annotation_check(get_text(token_num, page, length))
                    prev = "Annotation"
                elif page["classes"][token_num] == "KeyWords":
                    length = get_length(token_num, page)
                    if length < 2:
                        token_num += 1
                        continue
                    if len(mistakes[3]) == 0:
                        if layout[3] == 0:
                            layout[3] = layout_order
                            layout_order += 1
                        mistakes[3] = keywords_check(get_text(token_num, page, length), prev)
                    prev = "KeyWords"
                elif page["classes"][token_num] == "Affiliation":
                    length = get_length(token_num, page)
                    if length < 2:
                        token_num += 1
                        continue
                    if len(mistakes[4]) == 0:
                        if layout[4] == 0:
                            layout[4] = layout_order
                            layout_order += 1
                        mistakes[4] = affiliation_check(get_text(token_num, page, length),
                                                        len(get_lines(token_num, page, length)))
                    prev = "Affiliation"
                else:
                    length = get_length(token_num, page)
                    prev = "Other"
            else:
                if page["classes"][token_num] == "Header":
                    length = get_length(token_num, page)
                    text = get_text(token_num, page, length)
                    if "Figure" in text:
                        token_num = page["tokens"][token_num:].index("Figure") + len(page["tokens"][:token_num])
                        length = get_length(token_num, page)
                        if "Table" in text:
                            length = text.split(" ").index("Table")
                        mistakes[6] += figure_check(get_lines(token_num, page, length),
                                                    page["boxes"][token_num:token_num + length], width)
                    elif "Table" in text:
                        token_num = page["tokens"][token_num:].index("Table") + len(page["tokens"][:token_num])
                        length = get_length(token_num, page)
                        mistakes[6] += table_check(get_lines(token_num, page, length),
                                                   page["boxes"][token_num:token_num + length], width)
                    elif page["boxes"][token_num][0] < width / 4:
                        mistakes[5] += header_check(text)
                    prev = "Header"
                elif page["classes"][token_num] == "Text":
                    length = get_length(token_num, page)
                    if length > 2:
                        mistakes[6] += references_check(get_text(token_num, page, length))
                    prev = "Text"
                elif page["classes"][token_num] == "Reference":
                    if layout[5] == 0:
                        layout[5] = layout_order
                        layout_order += 1
                    length = get_length(token_num, page)
                    lines = get_lines(token_num, page, length)
                    for line in lines:
                        if re.fullmatch(r"\d+\.", line[0]):
                            num = line[0][:-1]
                            if references_len < num:
                                references_len = num
                    if re.fullmatch(r"[1-9]+\.", page["tokens"][token_num]):
                        num = int(page["tokens"][token_num][:-1])
                        if num > references_len:
                            references_len = num
                    prev = "Reference"
            token_num += max(length, 1)
        page_num += 1
    references_links = set(references_links)
    if len(references_links) < references_len:
        references = set(range(1, references_len))
        if len(references - references_links) == 1:
            mistakes[6] += [f"- в тексте не хватает ссылки на источник литературы с номером: {references - references_links}"]
        else:
            mistakes[6] += [f"- в тексте не хватает ссылок на источники литературы с номерами: {references - references_links}"]
    if layout != sorted(layout):
        for i in range(len(layout)):
            if layout[i] == 0:
                mistakes[i] += ["- раздел не обнаружен"]
        mistakes[7] += ["- cтатья должна иметь следующую структуру: название, список авторов, аннотация, список ключевых слов, аффилиации авторов, список литературы"]
    for i in range(7):
        mistakes[i] = list(set(mistakes[i]))
    return mistakes


function_words = ["of", "for", "an", "in", "the", "to", "at", "and", "by", "but", "if", "not", "a", "with", "on"]
id2label = {0: "Header", 1: "Header", 2: "Affiliation", 3: "Affiliation", 4: "Text", 5: "Text", 6: "Author", 7: "Author",
            8: "Annotation", 9: "Annotation", 10: "KeyWords", 11: "KeyWords", 12: "Reference", 13: "Reference",  14: "Other"}
