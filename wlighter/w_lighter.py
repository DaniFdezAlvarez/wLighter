import re

_PROP_DIRECT = "http://www.wikidata.org/prop/direct/"
_PROP_INDIRECT = "http://www.wikidata.org/prop/"
_ENTITY = "http://www.wikidata.org/entity/"
# _PROP_INDIRECT_STATEMENT = "http://www.wikidata.org/prop/statement/"

_SHEXC_FORMAT = "shexc"
_TURTLE_FORMAT = "turtle"


##### PARSERS

class AbstractParser(object):
    def __init__(self, raw_input, file_input):
        self._raw_input = raw_input
        self._file_input = file_input


    def yield_prefix_namespace_pairs(self):
        for a_line in self.yield_lines():
            for a_pair in self._yield_prefix_namespace_paris_in_line(a_line):
                yield a_pair

    def yield_lines(self):
        if self._raw_input is not None:
            for a_line in self._yield_raw_lines():
                yield a_line
        else:
            for a_line in self._yield_file_lines():
                yield a_line

    def _yield_raw_lines(self):
        for a_line in self._raw_input.split("\n"):
            yield a_line.strip()

    def _yield_file_lines(self):
        with open(self._file_input) as in_stream:
            for a_line in in_stream:
                yield a_line.strip()

    def _yield_prefix_namespace_paris_in_line(self, a_line):
        raise NotImplementedError()


class TurtleToyParser(AbstractParser):
    def __init__(self, raw_input, file_input):
        super().__init__(raw_input, file_input)

_SHEXC_PREFIX = re.compile("(^| )PREFIX ")
_SHEXC_PREFIX_SPEC = re.compile("([a-zA-Z]([a-zA-Z0-9\-]*[a-zA-Z0-9]+)?)? *: ")
_SHEXC_NAMESPACE_SPEC = re.compile("<[^ <>]+>")

class ShExCToyParser(AbstractParser):
    def _yield_prefix_namespace_paris_in_line(self, a_line):
        for a_match in re.finditer(_SHEXC_PREFIX, a_line):
            prefix = re.match(_SHEXC_PREFIX_SPEC, a_line[a_match.end(0):])
            prefix = str(prefix).replace(":" ,"").strip()  # Remove :
            namespace = re.match(_SHEXC_NAMESPACE_SPEC, a_line[a_match.end(0):])
            namespace = namespace[1:-1]  # Remove corners
            yield prefix, namespace


    def __init__(self, raw_input, file_input):
        super().__init__(raw_input, file_input)


class WLighter(object):

    def __init__(self, raw_input, file_input, format, languages, wikidata_alt_api):
        self._raw_input = raw_input
        self._file_input = file_input
        self._format = format
        self._languages = languages
        self._wikidata_alt_api = wikidata_alt_api

        self._parser = self._choose_parser()

        self._namespaces = None

        # These three may be provided
        self._namespace_entities = _ENTITY
        self._namespace_direct_prop = _PROP_DIRECT
        self._namespace_indirect_prop = _PROP_INDIRECT

        self._entity_full_pattern = None
        self._entity_prefixed_pattern = None
        self._prop_direct_full_pattern = None
        self._prop_direct_prefixed_pattern = None
        self._prop_indirect_full_pattern = None
        self._prop_indirect_prefixed_pattern = None



    def annotate_entities(self):
        pass

    def annotate_properties(self):
        pass

    def annotate_all(self):
        self._set_up()

        for a_line in self._parser.yield_lines():
            entity_mentions = self._look_for_entity_mentions(a_line)
            prop_mentions = self._look_for_prop_mentions(a_line)

    def _set_up(self):
        self._look_for_namespaces()
        self._compile_patterns()

    def _look_for_entity_mentions(self, a_line):
        full_mentions = re.findall(self._entity_full_pattern, a_line)
        if len(full_mentions) != 0:
            full_mentions = self._extract_id_from_full_uris(id_type="Q",
                                                            mentions_list=full_mentions)
        prefixed_mentions = re.findall(self._entity_prefixed_pattern, a_line)
        if len(full_mentions) != 0:
            prefixed_mentions = self._extract_id_from_prefixed_uris(id_type="Q",
                                                                     mentions_list=full_mentions)


        # todo : continue here

    def _look_for_entity_mentions(self, a_line):
        pass

    def _extract_id_from_full_uris(self, id_type, mentions_list):
        result = []
        for a_mention in mentions_list:
            a_mention = a_mention.strip()
            result.append(a_mention[a_mention.rfind(id_type):-1])
        return result

    def _extract_id_from_prefixed_uris(self, id_type, mentions_list):
        result = []
        for a_mention in mentions_list:
            a_mention = a_mention.strip()
            result.append(a_mention[a_mention.rfind(id_type):])
        return result


    def _compile_patterns(self):
        if self._entity_full_pattern is None :  # It should mean the rest are None too
            self._entity_full_pattern = re.compile("<" + self._namespace_entities + "Q[0-9]+" + ">")
            self._entity_prefixed_pattern = None if self._namespace_entities not in self._namespaces else \
                re.compile("(^| )" + self._namespaces[self._namespace_entities] + ":Q[0-9]+[ ?*+;]")

            self._prop_direct_full_pattern = re.compile("<" + self._namespace_direct_prop + "Q[0-9]+" + ">")
            self._prop_direct_prefixed_pattern = None if self._namespace_direct_prop not in self._namespaces else \
                re.compile("(^| )" + self._namespaces[self._namespace_direct_prop] + ":Q[0-9]+[ ?*+;]")

            self._prop_indirect_full_pattern = re.compile("<" + self._namespace_indirect_prop + "Q[0-9]+" + ">")
            self._prop_indirect_prefixed_pattern = None if self._namespace_indirect_prop not in self._namespaces else \
                re.compile("(^| )" + self._namespaces[self._namespace_indirect_prop] + ":Q[0-9]+[ ?*+;]")

    def _look_for_namespaces(self):
        if self._namespaces is None:
            self._namespaces = {}
            for a_prefix, a_namespace in self._parser.yield_prefix_namespace_pairs():
                self._namespaces[a_namespace] = a_prefix


    def _choose_parser(self):
        if self._format == _SHEXC_FORMAT:
            return ShExCToyParser(raw_input=self._raw_input,
                                  file_input=self._file_input)
        raise ValueError("Unsupported format: " + self._format)