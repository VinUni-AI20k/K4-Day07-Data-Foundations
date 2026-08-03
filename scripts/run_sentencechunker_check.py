import importlib

m = importlib.import_module('src')
SentenceChunker = m.SentenceChunker
SAMPLE_TEXT = (
    "The quick brown fox jumps over the lazy dog. "
    "A fox is a small omnivorous mammal. "
    "Dogs are loyal companions and working animals. "
    "Brown bears live in forests across the northern hemisphere. "
    "Jumping is a physical activity that requires leg strength. "
)

# test_returns_list
chunks = SentenceChunker(max_sentences_per_chunk=2).chunk(SAMPLE_TEXT)
assert isinstance(chunks, list), 'not list'
# test_respects_max_sentences
assert len(chunks) >= 2, 'expected >=2 chunks'
# test_single_sentence_max_gives_many_chunks
chunks_1 = SentenceChunker(max_sentences_per_chunk=1).chunk(SAMPLE_TEXT)
chunks_3 = SentenceChunker(max_sentences_per_chunk=3).chunk(SAMPLE_TEXT)
assert len(chunks_1) >= len(chunks_3), 'single sentence chunks should be >= 3-sentence chunks'
# test_chunks_are_strings
for c in chunks:
    assert isinstance(c, str), 'chunk not str'

print('SentenceChunker checks: OK')
