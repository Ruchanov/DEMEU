from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsNERTagger, Doc

segmenter = Segmenter()
morph_vocab = MorphVocab()
embedding = NewsEmbedding()
ner_tagger = NewsNERTagger(embedding)


def extract_entities(text):
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_ner(ner_tagger)

    entities = []
    for span in doc.spans:
        span.normalize(morph_vocab)
        entities.append({
            'text': span.text,
            'type': span.type,
            'normal': span.normal
        })
    return entities
