import docx
import json
import argparse
import sys
import glob
import os

def read_meta(fname):
    with open(fname, "rt", encoding="utf-8") as f:
        data = json.load(f)
    for i, doc_meta in enumerate(data):
        data[i]["color_map_rev"] = {v: k for k, v in data[i]["color_map"].items()}
    return data


def index_fonts():
    palette=[]
    with open("palette_729.txt") as f:
        for line in f:
            line=line.strip()
            if not line.startswith("#"):
                continue
            palette.append(line)
    #print(palette)
    assert len(palette)==len(set(palette))

    rgb_colors=[]
    for colorspec in palette:
        rgb_colors.append(colorspec[1:].upper())

    return rgb_colors

rgb_colors = index_fonts()
print(f"{len(rgb_colors)} unique colors available in color palette")



def yield_docs(docx_file):

    one_doc = {"doc_number": None, "doc_idx": None, "paragraphs": []}
    current_para = []
    for paragraph in docx_file.paragraphs:
        if len(current_para) > 0:
            assert one_doc["doc_number"] != None
            one_doc["paragraphs"].append(current_para)
            current_para = []
        for text_run in paragraph.runs:
            text = text_run.text
            
            # header line
            if text_run.bold == True:
                assert "numero" in text or "tunniste" in text, f"Suspicious bolded line: {text}"
                if "numero" in text:
                    if one_doc["doc_number"] != None: # new doc, yield previous
                        assert one_doc["doc_idx"] != None
                        yield one_doc
                        one_doc = {"doc_number": None, "doc_idx": None, "paragraphs": []}
                    one_doc["doc_number"] = text
                elif "tunniste" in text:
                    assert one_doc["doc_idx"] == None, f"{one_doc}, {text}"
                    one_doc["doc_idx"] = text
                else:
                    print("****", text)
                    assert False
                continue
                
            # normal text line
            color = str(text_run.font.color.rgb) if text_run.font.color.rgb is not None else None
            current_para.append((color, text))
            continue
    else:
        if len(current_para) > 0:
            assert one_doc["doc_number"] != None
            one_doc["paragraphs"].append(current_para)
        if one_doc["doc_number"] != None:
            yield one_doc


def return_next_markable(entity_map):

    markable = {"idx": None, "text": None, "annotation": None, "start": None, "end": None}
    for i, e_ids in enumerate(entity_map):
        if markable["idx"] != None:
            if markable["idx"] not in e_ids: # close the markable
                markable["end"] = i
                break
            continue
        if len(e_ids) > 0: # we do not have an open markable yet, start a new one
            markable["idx"] = e_ids[0]
            markable["start"] = i
    else:
        markable["end"] = i + 1
    # remove used ids
    for lidx in range(markable["start"], markable["end"]):
        tmp_list =  entity_map[lidx].copy()
        tmp_list.remove(markable["idx"])
        entity_map[lidx] = tmp_list
        
    return markable, entity_map
    

def build_markables(doc, meta):
    paragraphs = []
    markables = []
    global_char_idx = 0
    markable_counter = 0
    for paragraph in doc["paragraphs"]:
        raw_text = [] # raw text characters
        entity_map =[] # a list of entities for each character
        for color, text_span in paragraph:
            if color != None:
                assert color in rgb_colors, color
                color_idx = rgb_colors.index(color)
                entity = meta["color_map_rev"][color_idx].split("+")
            else:
                entity = []
            for c in text_span:
                raw_text.append(c)
                entity_map.append(entity)
        assert len(raw_text) == len(entity_map)
        paragraphs.append("".join(raw_text))
        
        while sum([len(l) for l in entity_map]) > 0:
        
            partial_markable, entity_map = return_next_markable(entity_map)

            # fill in the rest, and change local indices to global ones
            partial_markable["start"] = global_char_idx + partial_markable["start"]
            partial_markable["end"] = global_char_idx + partial_markable["end"]
            partial_markable["text"] = "".join(paragraphs)[partial_markable["start"]:partial_markable["end"]]
            partial_markable["counter"] = markable_counter
            markable_counter += 1
            markables.append(partial_markable)
            
            
        global_char_idx = len("".join(paragraphs))
        
            
    return paragraphs, markables
        
        


def main(args):

    all_data = []
    doc_counter = 0
    
    meta = read_meta(args.meta_json)
    for fname in sorted(glob.glob(os.path.join(args.input_dir, "*.docx"))):
        print("Reading", fname)

        doc = docx.Document(fname) # docx containing several documents
        
        for doc in yield_docs(doc):
            doc_meta = meta[doc_counter]
            print(doc["doc_number"])
            print(doc["doc_idx"])
            print("Doc metadata:", doc_meta["document number"], doc_meta["doc_id"])
            print()
            paragraphs, markables = build_markables(doc, doc_meta)
            
            full_text = "".join(paragraphs)
            for m in markables:
                assert m["text"] == full_text[m["start"]:m["end"]]
                
            d = {"doc_id": doc["doc_idx"], "doc_number": doc["doc_number"], "paragraphs": paragraphs, "annotations": markables}
            all_data.append(d)
                    
            doc_counter += 1
    
    print("Writing output to", args.output_json)
    with open(args.output_json, "wt", encoding="utf-8") as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)
            



if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", default=None, required=True, help="Input directory for docx files")
    parser.add_argument("--meta_json", default=None, required=True, help="Metadata json file")
    parser.add_argument("--output_json", default=None, required=True, help="Output json file")
    args = parser.parse_args()

    main(args)
