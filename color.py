import json
import docx
import argparse
import sys


def index_fonts():
    palette=[]
    with open("palette.txt") as f:
        for line in f:
            line=line.strip()
            if not line.startswith("#"):
                continue
            palette.append(line)
    #print(palette)
    assert len(palette)==len(set(palette))

    rgb_colors=[]
    for colorspec in palette:
        color=docx.shared.RGBColor.from_string(colorspec[1:].upper())
        rgb_colors.append(color)

    return rgb_colors

rgb_colors = index_fonts()
print(f"{len(rgb_colors)} unique colors available in palette.txt")


def make_spans(color_map, characters):
    result = []
    last_color = None
    current_text = []
    for color, c in zip(color_map, characters):
        if last_color is None or last_color == color:
            current_text.append(c)
            last_color = color
        else:
            assert last_color is not None and len(current_text) > 0
            result.append((last_color, "".join(current_text)))
            last_color = color
            current_text = [c]
    else:
        assert last_color is not None and len(current_text) > 0
        result.append((last_color, "".join(current_text)))
    return result




def color_doc(doc_text, doc_idx, annotations, output_doc):
    # p, p_idx_, doc
    total_len=0
    
    pgraph=output_doc.add_paragraph('')
    
    color_map=[[] for _ in range(len(doc_text))] # this will store the span information for each char in text, init with empty

    # iterate through annotations
    for markable in annotations:
        # {"idx": "1", "text": "Introduction", "annotation": "1-abstract-new-cf1-1-sgl", "start": 0, "end": 12, "counter": 0}
        if "-sgl" in markable["annotation"]:
            #print("Skipping singleton markable:", markable)
            continue
        for lst in color_map[markable["start"]:markable["end"]]:
            lst.append(markable["idx"])

    # make a lookup table such that each unique overlap of answer ids has a color of its own whew
    color_lookup = {"": -1}
    for span in color_map: # span is a list of all markables which overlap as id strings
        span = "+".join(span) # make it a single string
        color_lookup.setdefault(span, len(color_lookup))

    #colors=index_fonts()

    spans=make_spans(color_map, doc_text)

    for color, txt in spans:
        r = pgraph.add_run(txt)
        font_idx = color_lookup.get("+".join(color), None)
        if font_idx >= 0:
            if font_idx > len(rgb_colors) - 1:
                print(f"Warning, not enough colors, skipping {color}!!")
                continue
            r.font.color.rgb = rgb_colors[font_idx]

    total_len += len(doc_text) + 1

    return total_len, color_lookup


def main(args):

    with open(args.json, "rt", encoding="utf-8") as f:
        data = json.load(f)

    total_chars = 0

    doc = docx.Document()
    metadata = []
    
    for i, d in enumerate(data):
    
        p = doc.add_paragraph()
        t = f"Document number {i}"
        total_chars += len(t) + 1
        p.add_run(t).bold=True
        
        p = doc.add_paragraph()
        t = f"Document identifier: {d['doc_id']}"
        total_chars += len(t) + 1
        p.add_run(t).bold=True
        
        l , color_map = color_doc(d["text"], d["doc_id"], d["annotations"], doc)
        total_chars += l
        metadata.append({"document number": i, "doc_id": d["doc_id"], "color_map": color_map})
        
    print(f"Total number of characters in this docx: {total_chars}")

    with open(args.meta, "wt", encoding="utf-8") as f:
        json.dump(metadata, f)
    
    doc.save(args.docx)






if __name__=="__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=None, required=True, help="Input json file")
    parser.add_argument("--docx", default=None, required=True, help="Output docx file")
    parser.add_argument("--meta", default=None, required=True, help="Output metadata json file")
    args = parser.parse_args()
    
    main(args)

