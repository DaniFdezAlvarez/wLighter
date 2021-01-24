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
        with open(self._file_input, encoding="utf-8") as in_stream:
            for a_line in in_stream:
                yield a_line.rstrip()

    def _yield_prefix_namespace_paris_in_line(self, a_line):
        raise NotImplementedError()

    def is_prefix_line(self, line):
        raise NotImplementedError()


_TURTLE_PREFIX = re.compile("(^| )@prefix ")
_TURTLE_PREFIX_SPEC = re.compile("([a-zA-Z]([a-zA-Z0-9\-]*[a-zA-Z0-9]+)?)? *: ")
_TURTLE_NAMESPACE_SPEC = re.compile("<[^ <>]+>")

class TurtleToyParser(AbstractParser):

    def __init__(self, raw_input, file_input):
        super().__init__(raw_input, file_input)

    def _yield_prefix_namespace_paris_in_line(self, a_line):
        for a_match in re.finditer(_TURTLE_PREFIX, a_line):
            piece = a_line[a_match.end():]
            prefix = re.search(_TURTLE_PREFIX_SPEC, piece)
            prefix = piece[prefix.start():prefix.end()].replace(":", "").strip()  # Remove :
            namespace = re.search(_TURTLE_NAMESPACE_SPEC, a_line[a_match.end(0):])
            namespace = piece[namespace.start() + 1:namespace.end() - 1]  # Remove corners
            yield prefix, namespace

    def is_prefix_line(self, a_line):
        return a_line.startswith("@prefix ")



_SHEXC_PREFIX = re.compile("(^| )PREFIX ")
_SHEXC_PREFIX_SPEC = re.compile("([a-zA-Z]([a-zA-Z0-9\-]*[a-zA-Z0-9]+)?)? *: ")
_SHEXC_NAMESPACE_SPEC = re.compile("<[^ <>]+>")

_NO_LABEL = "(no label available)"
_MAX_IDS_PER_API_CALL = 49

_ENTITIES_API_CALL = "https://www.wikidata.org/w/api.php?action=wbgetentities&props=labels&ids={}&languages={}&format=json"


class ShExCToyParser(AbstractParser):

    def __init__(self, raw_input, file_input):
        super().__init__(raw_input, file_input)

    def _yield_prefix_namespace_paris_in_line(self, a_line):
        for a_match in re.finditer(_SHEXC_PREFIX, a_line):
            piece = a_line[a_match.end():]
            prefix = re.search(_SHEXC_PREFIX_SPEC, piece)
            prefix = piece[prefix.start():prefix.end()].replace(":", "").strip()  # Remove :
            namespace = re.search(_SHEXC_NAMESPACE_SPEC, a_line[a_match.end(0):])
            namespace = piece[namespace.start() + 1:namespace.end() - 1]  # Remove corners
            yield prefix, namespace

    def is_prefix_line(self, a_line):
        return a_line.startswith("PREFIX ")


######## FORMATTERS

_ARROW = " --> "
_SEP_SPACES = "    "


class BaseFormater(object):

    def __init__(self, out_file, string_return, parser, line_mentions_dict, chars_till_comment,
                 ids_dict, mode_column_aligned):
        self._out_file = out_file
        self._string_return = string_return
        self._parser = parser
        self._line_mentions_dict = line_mentions_dict
        self._chars_till_comment = chars_till_comment
        self._ids_dict = ids_dict
        self._mode_column_aligned = mode_column_aligned

        self._accumulated_result = None
        self._out_stream = None

    def produce_result(self):
        line_counter = 0
        for a_line in self._parser.yield_lines():
            if line_counter in self._line_mentions_dict:
                self._write_line_with_comments(line=a_line,
                                               comments=self._turn_entities_into_comments(
                                                   self._line_mentions_dict[line_counter])
                                               )
            else:
                self._write_line(line=a_line)
            line_counter += 1
        self._tear_down()
        return self._return_result()

    def set_up(self):
        if self._string_return:
            self._accumulated_result = []
        else:
            self._accumulated_result = None
        if self._out_file is not None:
            self._reset_file(self._out_file)
            self._out_stream = open(self._out_file, "wa")

    def _tear_down(self):
        if self._out_file is not None:
            self._out_stream.close()

    def _reset_file(self, out_file):
        with open(out_file, "w") as out_stream:
            out_stream.write("")

    def _turn_entities_into_comments(self, entity_mentions):
        if len(entity_mentions) == 0:
            return []
        result = []
        for a_mention in entity_mentions:
            result.append(self._turn_id_into_comment(id_wiki=a_mention,
                                                     label=self._ids_dict[a_mention]))
        return result

    def _turn_id_into_comment(self, id_wiki, label):
        return "{} {} {}".format(id_wiki,
                                 _ARROW,
                                 label)

    def _write_line_with_comments(self, line, comments):
        self._write_line(self._add_comments_to_line(line=line,
                                                    comments=comments))

    def _write_line(self, line):
        if self._accumulated_result is not None:
            self._accumulated_result.append(line)
        if self._out_stream is not None:
            self._out_stream.write(line + "\n")

    def _return_result(self):
        if self._string_return:
            return "\n".join(self._accumulated_result)

    def _propper_amount_of_spaces(self, line_length):
        if self._mode_column_aligned:
            return " " * (self._chars_till_comment - line_length)
        else:
            return _SEP_SPACES

    def _add_comments_to_line(self, line, comments):
        raise NotImplementedError()


_RDFS_NAMESPACE = "http://www.w3.org/2000/01/rdf-schema#"


class RdfsCommentFormatter(BaseFormater):

    def __init__(self, out_file, string_return, parser,
                 line_mentions_dict, chars_till_comment, ids_dict,
                 namespaces_dict, mode_column_aligned):
        super().__init__(out_file=out_file,
                         string_return=string_return,
                         parser=parser,
                         line_mentions_dict=line_mentions_dict,
                         chars_till_comment=chars_till_comment,
                         ids_dict=ids_dict,
                         mode_column_aligned=mode_column_aligned)

        self._rdfs_prefix = None
        self._added_rdfs = False

        self._set_rdfs_namespace(namespaces_dict)  # Give a value to the provious atts

    def _set_rdfs_namespace(self, namespaces_dict):
        if _RDFS_NAMESPACE in namespaces_dict:
            self._rdfs_prefix = namespaces_dict[_RDFS_NAMESPACE]
            self._added_rdfs = False
            return
        curr_prefixes = namespaces_dict.values()
        if "rdfs" not in curr_prefixes:
            self._rdfs_prefix = "rdfs"
            self._added_rdfs = True
            return
        counter = 2
        candidate = "rdfs" + str(counter)
        while candidate in curr_prefixes:
            counter += 1
            candidate = "rdfs" + str(counter)
        self._rdfs_prefix = candidate
        self._added_rdfs = True

    def _add_comments_to_line(self, line, comments):
        return line + self._propper_amount_of_spaces(len(line)) + '// {}:comment "{}"'.format(self._rdfs_prefix,
                                                                                              " ; ".join(comments))

    def produce_result(self):
        if self._added_rdfs:
            self._write_line("PREFIX {}: <{}>".format(self._rdfs_prefix, _RDFS_NAMESPACE))
        return super().produce_result()


class RawCommentsFormatter(BaseFormater):

    def __init__(self, out_file, string_return, parser, line_mentions_dict,
                 chars_till_comment, ids_dict, mode_column_aligned):
        super().__init__(out_file=out_file,
                         string_return=string_return,
                         parser=parser,
                         line_mentions_dict=line_mentions_dict,
                         chars_till_comment=chars_till_comment,
                         ids_dict=ids_dict,
                         mode_column_aligned=mode_column_aligned)

    def _add_comments_to_line(self, line, comments):
        return line + self._propper_amount_of_spaces(len(line)) + "# " + " ; ".join(comments)


class WLighter(object):

    def __init__(self, raw_input=None, file_input=None, format=_SHEXC_FORMAT, languages=None,
                 generate_rdfs_comments=False, mode_column_aligned=True):
        self._raw_input = raw_input
        self._file_input = file_input
        self._format = format
        self._languages = ["en"] if languages is None else languages
        self._generate_rdfs_comments = generate_rdfs_comments
        self._mode_column_aligned = mode_column_aligned

        self._parser = self._choose_parser()
        self._formatter = None  # Will be Chosen later

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

        self._line_mentions_dict = {}
        self._ids_dict = {}

    def annotate_entities(self, out_file, string_return):
        return self._base_annotate(out_file=out_file,
                                   string_return=string_return,
                                   look_for_mentions_func=self._look_for_entity_mentions)

    def annotate_properties(self, out_file=None, string_return=True):
        return self._base_annotate(out_file=out_file,
                                   string_return=string_return,
                                   look_for_mentions_func=self._look_for_prop_mentions)

    def annotate_all(self, out_file=None, string_return=True):
        return self._base_annotate(out_file=out_file,
                                   string_return=string_return,
                                   look_for_mentions_func=self._look_for_all_mentions)

    def _base_annotate(self, out_file, string_return, look_for_mentions_func):
        self._set_up(out_file)
        max_lenght = 0
        line_counter = 0
        for a_line in self._parser.yield_lines():
            if not self._parser.is_prefix_line(a_line):
                max_lenght = len(a_line) if len(a_line) > max_lenght else max_lenght
            self._save_mentions(line_number=line_counter,
                                mentions=look_for_mentions_func(a_line))
            line_counter += 1

        self._set_formatter(out_file, string_return, max_lenght + 2)
        self._solve_mentions()
        return self._formatter.produce_result()

    def _look_for_all_mentions(self, line):
        entity_mentions = self._look_for_entity_mentions(line)
        prop_mentions = self._look_for_prop_mentions(line)
        return entity_mentions.union(prop_mentions)

    def _set_formatter(self, out_file, string_return, max_length):
        if self._generate_rdfs_comments:
            self._formatter = RdfsCommentFormatter(out_file=out_file,
                                                   string_return=string_return,
                                                   parser=self._parser,
                                                   line_mentions_dict=self._line_mentions_dict,
                                                   chars_till_comment=max_length,
                                                   ids_dict=self._ids_dict,
                                                   namespaces_dict=self._namespaces,
                                                   mode_column_aligned=self._mode_column_aligned)
        else:
            self._formatter = RawCommentsFormatter(out_file=out_file,
                                                   string_return=string_return,
                                                   parser=self._parser,
                                                   line_mentions_dict=self._line_mentions_dict,
                                                   chars_till_comment=max_length,
                                                   ids_dict=self._ids_dict,
                                                   mode_column_aligned=self._mode_column_aligned)
        self._formatter.set_up()

    def _solve_mentions(self):
        m_count = 0
        curr_group = []
        for a_mention in self._ids_dict:
            curr_group.append(a_mention)
            m_count += 1
            if m_count % _MAX_IDS_PER_API_CALL == 0:
                self._entities_api_call(curr_group)
                curr_group = []
        if len(curr_group) > 0:
            self._entities_api_call(curr_group)

    def _save_mentions(self, line_number, mentions):
        if len(mentions) > 0:
            self._line_mentions_dict[line_number] = mentions
            for a_mention in mentions:
                if a_mention not in self._ids_dict:
                    self._ids_dict[a_mention] = None

    def _tear_down(self):
        if self._out_stream is not None:
            self._out_stream.close()
        self._out_stream = None

    def _build_languages_for_api(self):
        if len(self._languages) == 0:
            return "en"
        result = "|".join(self._languages)
        if "en" in self._languages:
            return result
        else:
            return result + "|en"

    def _entities_api_call(self, entity_goup):
        response = requests.get(_ENTITIES_API_CALL.format("|".join(entity_goup),
                                                          self._languages_for_api))
        response = response.json()
        for an_entity in entity_goup:
            self._ids_dict[an_entity] = \
                self._get_label_from_json_result(labels_entity_json=
                                                 response["entities"][an_entity]["labels"])

    def _get_label_from_json_result(self, labels_entity_json):
        for a_language in self._languages:
            if a_language in labels_entity_json:
                return labels_entity_json[a_language]["value"]
        if "en" in labels_entity_json:
            return labels_entity_json["en"]["value"]
        return _NO_LABEL

    def _set_up(self, out_file):
        if self._file_input is not None and self._file_input == out_file:
            raise ValueError("Please, do not use the same disk path as input and output at a time")
        self._line_mentions_dict = {}
        self._ids_dict = {}
        self._look_for_namespaces()
        self._compile_patterns()

    def _look_for_entity_mentions(self, a_line):
        full_mentions = re.findall(self._entity_full_pattern, a_line)
        if len(full_mentions) != 0:
            full_mentions = self._extract_id_from_full_uris(id_type="Q",
                                                            mentions_list=full_mentions)
        if self._entity_prefixed_pattern is not None:
            prefixed_mentions = re.findall(self._entity_prefixed_pattern, a_line)
            if len(prefixed_mentions) != 0:
                prefixed_mentions = self._extract_id_from_prefixed_uris(id_type="Q",
                                                                        mentions_list=full_mentions)
            return set(full_mentions + prefixed_mentions)
        return set(full_mentions)

    def _look_for_prop_mentions(self, a_line):
        full_mentions = re.findall(self._prop_direct_full_pattern, a_line)
        full_mentions += re.findall(self._prop_indirect_full_pattern, a_line)
        if len(full_mentions) != 0:
            full_mentions = self._extract_id_from_full_uris(id_type="P",
                                                            mentions_list=full_mentions)

        prefixed_mentions = []
        if self._prop_direct_prefixed_pattern is not None:
            prefixed_mentions += re.findall(self._prop_direct_prefixed_pattern, a_line)
        if self._prop_indirect_prefixed_pattern is not None:
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
        if self._entity_full_pattern is None:  # It should mean the rest are None too
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
        elif self._format == _TURTLE_FORMAT:
            return TurtleToyParser(raw_input=self._raw_input,
                                   file_input=self._file_input)
        raise ValueError("Unsupported format: " + self._format)
