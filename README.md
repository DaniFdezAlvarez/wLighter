# wLighter

wLighter is a Python library to annotate ShEx or RDF files containing Wikidata entities and properties. 

Wikidata identifies properties witn an ID such as "PXXX" and entities with IDs such as "QXXX", where XXX is a number with no relation with the concept represented by the ID. This causes that text files containing many Wikidata IDs are quite hard to understand.

wLighter is a simple library built on top of the Wikidata API. It expect to receive RDF or ShEx content where some Wikidata URIs are used. It returns the same content with annotations (comments) in which each Wikidata ID is associated to its label.

You can specify in which language you prefer the labels. wLighter will try to get the label for your preferred language(s), or get the English one in case some ID has no label in your selected language. 

When working with ShEx, you can also select if you prefer to generate inline comments using '# QXX --> Example' or rdfs inline annotation such as '// rdfs:comment  "QXX --> Example"'.

You can also choose to provide your input or get your output via string or reading some file's content.

*The input formats currently supported are ShExC and Turtle.*

Please, contact the author or feel free to add an issue to this repository if you find a bug or have some feature request. 

## Instalation

You can install wLighter using pip. Execute the following command:

    $ pip install wlighter

If you prefer to use wLighter by source with git clone, ensure you execute it in an enviroment with the dependencies listed in requirements.txt.
You can install those dependencies by using the following command:

    $ pip install -r requirements.txt

## Example code

The following example code takes a ShEx file placed in wiki_test_file.shex and annotates it generating inline rdfs:comments. The result is returned as a string. The preferred language for the labels is Spanish. In case there is not a label in Spanish for a given element, then wLighter will use the French one. If French is missing too, then the English one. 


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

