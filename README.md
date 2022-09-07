# corefud-finnish-translation

CorefUD 1.0 coreference data machine translated to Finnish. Currently including translations of English-GUM and Czech-PCEDT.

# Files

* `translation-inputs/treebank/{train,dev}/{train,dev}.json`: Original data converted from conllu into json (produced by runnning `conllu2json.py`)
* `translation-inputs/treebank/{train,dev}/*.docx`: Original data converted to docx in order to translate it (produced by running `color.py`)
* `translation-inputs/treebank/{train,dev}/meta.json`: Metadata needed when converting docx files back to json (produced by running `color.py`)

* `translation-outputs/treebank/{train,dev}/*.docx`: Docx files translated to Finnish (produced by DeepL service)
* `translation-outputs/treebank/{train,dev}/{train,dev}.json`: Translated docx files converted to json (produced by running `docx2json.py`)


Note that during conversion/translation, some of the information available in the original datasets is lost. The translated data includes annotations for mention spans (singleton mentions were not translated) and coreference cluster identifiers for each mention.

# Usage

Visualize coreference clusters:

`python3 group_mentions.py --file translation-outputs/treebank/{train,dev}/{train,dev}.json | less`

Each mention in the json format includes a start and end index for slicing, given as global character indices for the full, concatenated document text (`document_text = "".join(paragraphs)`). Therefore, `mention["text"] == document_text[mention["start"]:mention["end"]]`.


# Licenses

### Code

CC BY-SA 4.0

### Translated Finnish data

CC BY-NC-SA 4.0

The translations are made using the DeepL service and the following restrictions on its use apply from the DeepL terms and conditions:
* This data cannot be used in Machine Translation system training, development, and evaluation
* This data cannot be used to evaluate the DeepL system against other Machine Translation systems

### Original datasets

English-GUM: CC BY-NC-SA 4.0

Czech-PCEDT: CC BY-NC-SA 3.0


# References

### Finnish translations

Not yet published, but please acknowledge if you use this in your work.

### Original datasets

CorefUD:
* Nedoluzhko, Anna; et al., 2022, Coreference in Universal Dependencies 1.0 (CorefUD 1.0), LINDAT/CLARIAH-CZ digital library at the Institute of Formal and Applied Linguistics (ÚFAL), Faculty of Mathematics and Physics, Charles University, http://hdl.handle.net/11234/1-4698.

English-GUM:
* Zeldes, A. (2017). The GUM Corpus: Creating Multilayer Resources in the Classroom. Language Resources and Evaluation, 51(3):581–612.

Czech-PCEDT:
* Nedoluzhko, A., Novák, M., Cinková, S., Mikulová, M., and Mírovský, J. (2016). Coreference in Prague Czech-English Dependency Treebank.  In Proceedings of the Tenth International Conference on Language Resources and Evaluation (LREC'16), pages 169–176, Portorož, Slovenia. European Language Resources Association.
