

import json
import argparse
import re

opening_markable_re = re.compile("(?:\((?P<complete>(?P<completeidx>[0-9]+)[^\(\)]+)\))|(?:\((?P<opening>(?P<openingidx>[0-9]+)\-[^\(\)]+))")
closing_markable_re = re.compile("(?:^|\))([0-9]+)")

def yield_docs(f):

    doc_lines = []
    for line in f:
        if "# newdoc" in line:
            if len(doc_lines) > 0:
                assert "# newdoc id =" in doc_lines[0]
                doc_id = doc_lines[0].split("=", 1)[-1].strip()
                yield doc_id, doc_lines
                doc_lines = []
        doc_lines.append(line.strip())
    else:
        if len(doc_lines) > 0:
            assert "# newdoc id =" in doc_lines[0]
            doc_id = doc_lines[0].split("=", 1)[-1].strip()
            yield doc_id, doc_lines
            
            
ID,FORM,LEMMA,UPOS,XPOS,FEAT,HEAD,DEPREL,DEPS,MISC=range(10)

def yield_sents(lines):
    sent=[]
    comment=[]
    for line in lines:
        line=line.strip()
        if not line: # new sentence
            if sent:
                yield comment,sent
            comment=[]
            sent=[]
        elif line.startswith("#"):
            comment.append(line)
        else: #normal line
            sent.append(line.split("\t"))
    else:
        if sent:
            yield comment, sent
            

def is_new_paragraph(comms):
    for c in comms:
        c = c.strip()
        if c == "# newpar":
            return True
    return False
    
def get_text(comm):
    for c in comm:
        c = c.strip()
        if "# text =" in c:
            _, text = c.split("=", 1)
            return text.strip()
    assert False, "Raw text not found from the comments!!!"

def gather_doc_text(doc):
    raw_text = ""
    next_space=""
    for comm, sent in yield_sents(doc):
        if is_new_paragraph(comm):
            if raw_text != "":
                raw_text = raw_text + "\n\n"
            next_space=""
        sent_text = get_text(comm)
        raw_text = raw_text + next_space + sent_text
        next_space = " " if "SpaceAfter=No" not in sent[-1][MISC] else " "
    return raw_text
            
def get_entity_annotation(misc):

    annotations = misc.split("|")
    for ann in annotations:
        cat, value = ann.split("=", 1) if ann != "_" else (None, None)
        if cat == "Entity":
            return value
    return "_"

def return_latest_markable(open_markables, idx):
    for i in range(len(open_markables)-1, -1, -1): # iterate in reverse order
        if open_markables[i]["idx"] == idx:
            return i
    print(idx)
    print(open_markables)
    assert False, f"closing idx {idx} not found from open markables"

# Entity=(7-abstract-new-cf6-2-coref(3-abstract-giv:act-cf1-1-coref)
# global.Entity = GRP-etype-infstat-centering-minspan-link-identity

# GRP = coreference group
# etype = entity type
# infstat = information status
# centering = centering theory annotation
# minspan = minimal span of tokens for head matching
# link = coreference link type
# identity = named entity identity (if available)

    
def get_token_index(current, token, doc):
    while True:
        if doc[current:current+len(token)] == token:
            return current, current+len(token)
        current += 1


def yield_markables(doc, doc_text):
    # doc = conllu lines
    # doc_text = original, raw text constructed from the conllu
    
    counter = 0
    open_markables = []
    current_char_index = 0 # where are we going in terms of raw text
    for comm, sent in yield_sents(doc):
        for i, token in enumerate(sent):
            # skip nulls and multiword tokens 
            if "." in token[ID] or "-" in token[ID]: # ok to skip as these are not part of raw text (multiword is always token 1 + token 2 in this corpus)
                continue
            
            entity_annotation = get_entity_annotation(token[MISC])
            
            token_start, token_end = get_token_index(current_char_index, token[FORM], doc_text) # token is doc_text[token_start:token_end]
            current_char_index = token_end
                
            # (1) find all opened markables (complete or partial) from annotation
            for hit in opening_markable_re.findall(entity_annotation):
                if hit[0] != "": # complete markable
                    yield {"idx": hit[1], "text": doc_text[token_start:token_end], "annotation": hit[0], "start": token_start, "end": token_end, "counter": counter}
                    counter += 1
                else: # partial
                    open_markables.append({"idx": hit[3], "text": None, "annotation": hit[2], "start": token_start, "end": None})
                   
            # (2) close the markables from annotation
            for idx in closing_markable_re.findall(entity_annotation):
                data = open_markables.pop(return_latest_markable(open_markables, idx))
                data["text"] = doc_text[data["start"]:token_end]
                data["end"] = token_end
                data["counter"] = counter
                counter += 1
                yield data

    else:
        if len(open_markables) > 0:
            print("\nThere are still open markables when the document ends!!!\n")
            print(open_markables)
            assert False
        
def main(args):

    all_annotations = []
    with open(args.file, "rt", encoding="utf-8") as f:
        for i, (doc_id, doc) in enumerate(yield_docs(f)):
            doc_text = gather_doc_text(doc)
            markables = []
            for markable in yield_markables(doc, doc_text):
                markables.append(markable)
                
            d = {"doc_id": doc_id, "text": doc_text, "annotations": markables}
            all_annotations.append(d)
                
    with open(args.output, "wt", encoding="utf-8") as f:
        json.dump(all_annotations, f, indent=4, ensure_ascii=False)
                

    
        
if __name__=="__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=None, required=True, help="Input file")
    parser.add_argument("--output", default=None, required=True, help="Output file name")
    args = parser.parse_args()
    
    
    # TODO: better representation of paragraphs?
    
    main(args)
