import re
import requests

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
            yield a_line.rstrip()

    def _yield_file_lines(self):
        with open(self._file_input) as in_stream:
            for a_line in in_stream:
                yield a_line.rstrip()

    def _yield_prefix_namespace_paris_in_line(self, a_line):
        raise NotImplementedError()


class TurtleToyParser(AbstractParser):
    def __init__(self, raw_input, file_input):
        super().__init__(raw_input, file_input)

_SHEXC_PREFIX = re.compile("(^| )PREFIX ")
_SHEXC_PREFIX_SPEC = re.compile("([a-zA-Z]([a-zA-Z0-9\-]*[a-zA-Z0-9]+)?)? *: ")
_SHEXC_NAMESPACE_SPEC = re.compile("<[^ <>]+>")

_NO_LABEL = "(no label available)"
_ARROW = " --> "
_SEP_SPACES = "    "


_ENTITIES_API_CALL = "https://www.wikidata.org/w/api.php?action=wbgetentities&props=labels&ids={}&languages={}&format=json"
class ShExCToyParser(AbstractParser):
    def _yield_prefix_namespace_paris_in_line(self, a_line):
        for a_match in re.finditer(_SHEXC_PREFIX, a_line):
            piece = a_line[a_match.end():]
            prefix = re.search(_SHEXC_PREFIX_SPEC, piece)
            prefix = piece[prefix.start():prefix.end()].replace(":" ,"").strip()  # Remove :
            namespace = re.search(_SHEXC_NAMESPACE_SPEC, a_line[a_match.end(0):])
            namespace = piece[namespace.start()+1:namespace.end()-1]  # Remove corners
            yield prefix, namespace


    def __init__(self, raw_input, file_input):
        super().__init__(raw_input, file_input)


class WLighter(object):

    def __init__(self, raw_input=None, file_input=None, format=_SHEXC_FORMAT, languages=None):
        self._raw_input = raw_input
        self._file_input = file_input
        self._format = format
        self._languages = ["en"] if languages is None else languages

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
        self._languages_for_api = self._build_languages_for_api()

        self._cache = {}

        self._out_stream = None
        self._accumulated_result = None

        self._line_mentions_dict = {}
        self._ids_dict = {}



    def annotate_entities(self, out_file, string_return):
        self._set_up(out_file=out_file, string_return=True)
        for a_line in self._parser.yield_lines():
            comments = None
            entity_mentions = self._look_for_entity_mentions(a_line)
            if len(entity_mentions) != 0:
                comments += self._turn_entities_into_comments(entity_mentions)
            self._write_line(line=a_line,
                             comments=comments)
        self._tear_down()
        return self._return_result(string_return)

    def annotate_properties(self, out_file=None, string_return=True):
        self._set_up(out_file, string_return)
        for a_line in self._parser.yield_lines():
            comments = None
            prop_mentions = self._look_for_prop_mentions(a_line)
            if len(prop_mentions) != 0:
                comments = self._turn_entities_into_comments(prop_mentions)
            self._write_line(line=a_line,
                             comments=comments)
        self._tear_down()
        return self._return_result(string_return)


    def annotate_all(self, out_file=None, string_return=True):
        self._set_up(out_file, string_return)
        max_lenght = 0
        line_counter = 0
        for a_line in self._parser.yield_lines():

            max_lenght = len(a_line) if len(a_line) > max_lenght else max_lenght
            entity_mentions = self._look_for_entity_mentions(a_line)
            prop_mentions = self._look_for_prop_mentions(a_line)
            self.save_
            self._line_counter += 1

        # TODO MOVE THIS STUFF FROM HERE!
            if len(entity_mentions) != 0 or len(prop_mentions) != 0:
                comments = self._turn_entities_into_comments(prop_mentions)  # first the props
                comments += self._turn_entities_into_comments(entity_mentions)
            self._write_line(line=a_line,
                             comments=comments)
        self._tear_down()
        return self._return_result(string_return)

    def _write_line(self, line, comments):
        target_line = line if comments is None else self._add_comments_to_line(line, comments)
        if self._accumulated_result is not None:
            self._accumulated_result.append(target_line)
        if self._out_stream is not None:
            self._out_stream.write(target_line + "\n")

    def _add_comments_to_line(self, line, comments):
        return line + _SEP_SPACES + "# " + ";".join(comments)

    def _tear_down(self):
        if self._out_stream is not None:
            self._out_stream.close()
        self._out_stream = None

    def _return_result(self, string_return):
        if string_return:
            return "\n".join(self._accumulated_result)


    def _build_languages_for_api(self):
        if len(self._languages) == 0:
            return "en"
        result = "|".join(self._languages)
        if "en" in self._languages:
            return result
        else:
            return result + "|en"


    def _turn_entities_into_comments(self, entity_mentions):
        if len(entity_mentions) == 0:
            return []
        result = []
        for a_mention in entity_mentions:
            label = self._solve_entity_label(a_mention)
            result.append(self._turn_id_into_comment(id_wiki=a_mention,
                                                     label=label))
        return result


    def _turn_id_into_comment(self, id_wiki, label):
        return "{} {} {}".format(id_wiki,
                                 _ARROW,
                                 label)

    def _solve_entity_label(self, entity):
        if entity in self._cache:
            return self._cache[entity]
        else:
            result = self._entity_api_call(entity)
            self._cache[entity] = result
            return result


    def _entity_api_call(self, entity):
        response = requests.get(_ENTITIES_API_CALL.format(entity,
                                                          self._languages_for_api))
        response = response.json()
        labels = response["entities"][entity]["labels"]
        for a_language in self._languages:
            if a_language in labels:
                return labels[a_language]["value"]
        if "en" in labels:
            return labels["en"]["value"]
        return _NO_LABEL


    def _set_up(self, out_file, string_return):
        if self._file_input is not None and self._file_input == out_file:
            raise ValueError("Please, do not use the same disk path as input and output at a time")
        self._line_mentions_dict = {}
        self._ids_dict = {}
        self._look_for_namespaces()
        self._compile_patterns()
        if string_return:
            self._accumulated_result = []
        else:
            self._accumulated_result = None
        if out_file is not None:
            self._reset_file(out_file)
            self._out_stream = open(out_file, "wa")

    def _reset_file(self, out_file):
        with open(out_file, "w") as out_stream:
            out_stream.write("")


    def _look_for_entity_mentions(self, a_line):
        full_mentions = re.findall(self._entity_full_pattern, a_line)
        if len(full_mentions) != 0:
            full_mentions = self._extract_id_from_full_uris(id_type="Q",
                                                            mentions_list=full_mentions)
        prefixed_mentions = re.findall(self._entity_prefixed_pattern, a_line)
        if len(prefixed_mentions) != 0:
            prefixed_mentions = self._extract_id_from_prefixed_uris(id_type="Q",
                                                                    mentions_list=full_mentions)

        return set(full_mentions + prefixed_mentions)

    def _look_for_prop_mentions(self, a_line):
        full_mentions = re.findall(self._prop_direct_full_pattern, a_line)
        full_mentions += re.findall(self._prop_indirect_full_pattern, a_line)
        if len(full_mentions) != 0:
            full_mentions = self._extract_id_from_full_uris(id_type="P",
                                                            mentions_list=full_mentions)

        prefixed_mentions = re.findall(self._prop_direct_prefixed_pattern, a_line)
        prefixed_mentions += re.findall(self._prop_indirect_prefixed_pattern, a_line)
        if len(prefixed_mentions) != 0:
            prefixed_mentions = self._extract_id_from_prefixed_uris(id_type="P",
                                                                    mentions_list=prefixed_mentions)

        return set(full_mentions + prefixed_mentions)



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
                re.compile("(?:^| )" + self._namespaces[self._namespace_entities] + ":Q[0-9]+[ ?*+;]")

            self._prop_direct_full_pattern = re.compile("<" + self._namespace_direct_prop + "P[0-9]+" + ">")
            self._prop_direct_prefixed_pattern = None if self._namespace_direct_prop not in self._namespaces else \
                re.compile("(?:^| )" + self._namespaces[self._namespace_direct_prop] + ":P[0-9]+[ ?*+;]")

            self._prop_indirect_full_pattern = re.compile("<" + self._namespace_indirect_prop + "P[0-9]+" + ">")
            self._prop_indirect_prefixed_pattern = None if self._namespace_indirect_prop not in self._namespaces else \
                re.compile("(?:^| )" + self._namespaces[self._namespace_indirect_prop] + ":P[0-9]+[ ?*+;]")

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