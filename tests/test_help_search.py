"""Recherche dans l'aide (sans Qt) : help_search.py, repris de Varians.
Sans tenir compte des accents ni de la casse ; plusieurs mots : les
sections qui les contiennent tous ; entre guillemets, l'expression exacte."""
from __future__ import annotations

from varians_synchro.help_search import Section, Utf16Positions, fold, query_terms, search

TEXT = ("Témoin pivot\n"
        "Le témoin pivot sert de référence : « Aligner les témoins » le relie à chaque autre.\n"
        "Exporter\n"
        "Les JSON validés sont dans validated/ : l’export écrit aussi working/.\n")
FIRST = TEXT.index("Exporter")
SECTIONS = [Section("Témoin pivot", 0, FIRST), Section("Exporter", FIRST, len(TEXT))]


def test_the_text_is_folded_without_accents_case_or_typographic_signs():
    folded, origin = fold("Témoin l’œuvre « x »")
    assert folded == "temoin l'œuvre \" x \""
    assert len(origin) == len(folded) and origin[:3] == [0, 1, 2]
    assert fold("Straße")[0] == "strasse"
    assert fold("Straße")[1] == [0, 1, 2, 3, 4, 4, 5]


def test_the_query_gives_words_and_quoted_phrases():
    assert query_terms("temoin PIVOT") == ["temoin", "pivot"]
    assert query_terms('"aligner les temoins" json') == ["aligner les temoins", "json"]
    assert query_terms("« Aligner les témoins »") == ["aligner les temoins"]
    assert query_terms("   ") == []


def test_a_section_must_contain_every_word():
    hits = search(TEXT, SECTIONS, "temoin REFERENCE")
    assert [hit.section.title for hit in hits] == ["Témoin pivot"]
    # « témoins » : l'occurrence couvre le mot cherché, « témoin ».
    assert {TEXT[a:b] for a, b in hits[0].spans} == {"Témoin", "témoin", "référence"}
    assert search(TEXT, SECTIONS, "pivot json") == []           # deux sections différentes
    assert search(TEXT, SECTIONS, "") == []


def test_accents_case_and_apostrophes_do_not_matter():
    hits = search(TEXT, SECTIONS, "l'export validated")
    assert [hit.section.title for hit in hits] == ["Exporter"]
    assert "l’export" in [TEXT[a:b] for a, b in hits[0].spans]


def test_a_quoted_phrase_is_found_as_a_whole():
    hits = search(TEXT, SECTIONS, '"aligner les temoins"')
    assert [TEXT[a:b] for a, b in hits[0].spans] == ["Aligner les témoins"]
    assert search(TEXT, SECTIONS, '"temoins les aligner"') == []


def test_each_hit_has_a_one_line_excerpt_around_its_first_occurrence():
    excerpt = search(TEXT, SECTIONS, "validated", context=12)[0].excerpt
    assert "validated" in excerpt and "\n" not in excerpt
    assert excerpt.startswith("…") and excerpt.endswith("…")


def test_positions_beyond_the_basic_plane_count_twice_for_qt():
    positions = Utf16Positions("a𝔄b")
    assert [positions.qt(i) for i in range(4)] == [0, 1, 3, 4]
    assert [positions.python(p) for p in (0, 1, 3, 4)] == [0, 1, 2, 3]
