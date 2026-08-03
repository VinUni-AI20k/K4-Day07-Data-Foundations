import sys
from pathlib import Path

# Ensure project root on path for direct script execution
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from ingest import load_documents
from src.chunking import ChunkingStrategyComparator


docs = load_documents('data/k4_shopee')
names = ['chinh-sach-van-chuyen','chinh-sach-tra-hang-hoan-tien','cach-dong-goi-don-hoan-tra']
comp = ChunkingStrategyComparator()
for name in names:
    doc = next((d for d in docs if d.id==name), None)
    if not doc:
        print('missing', name)
        continue
    res = comp.compare(doc.content, chunk_size=200)
    print('\nDocument:', name)
    for k,v in res.items():
        print(k, 'count=', v['count'], 'avg_len=', round(v['avg_length'],1))
