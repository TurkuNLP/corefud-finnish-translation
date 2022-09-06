import json
import argparse

def main(args):

    with open(args.file, "rt", encoding="utf-8") as f:
        data = json.load(f)
        
    for doc in data:
        mentions = {}
        for m in doc["annotations"]:
            if m["idx"] not in mentions:
                mentions[m["idx"]] = []
            mentions[m["idx"]].append(m)
            
        for key, values in mentions.items():
            print("Key:", key)
            for v in values:
                print(v)
            print()
        


if __name__=="__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=None, required=True, help="Input file")
    args = parser.parse_args()
    
    
    main(args)
