# wLighter

wLighter is a python library to annotate ShEx or RDF files containing Wikidata entities and properties. 

Wikidata identifies properties witn an ID such as "PXXX" and entities with IDs such as "QXXX", where XXX is a number with no relacion with the idea related to the ID. This causes that text files containing many Wikidata IDs are quite hard to understand.

wLighter is a simple library built on top of the Wikidata API. It receives a file/string containing Wikidata IDs and return the same file with annotated with comments in which each Wikidata ID is associated with its label.

You can specify in which language do you prefer the labels. wLighter will try to get the label for your preferred language(s), or get the English one in case some ID has no label in your selected language. 

When working with ShEx, you can also select if you prefer to generate normal inline comments using '# QXX --> Example' or rdfs inline annotation such as '// rdfs:comment  "QXX --> Example"'.

You can also choose to provide your input/get your output via normal string of reading some file content.

*The input format currently supported are ShExC and Turtle.*

## Instalation


## Example code

The following example code takes a ShEx file placed in wiki_test_file.shex and annotates it generating inline rdfs:comments. The result is returned as a normal string. The preferred language for the labels is Spanish. In case there is not a label in Spanish for a givne element, then it wLighter will use the french one. If French is missing too, then the English one. 


```python
from wlighter import WLighter, SHEXC_FORMAT

target_file = "wiki_test_file.shex"

wlig = WLighter(file_input=target_file,
                format=SHEXC_FORMAT,
                languages=["es", "fr"],
                generate_rdfs_comments=True)
result = wlig.annotate_all(string_return=True)
print(result)

```

