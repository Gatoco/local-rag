#!/usr/bin/env python3
"""
Efficient RAG Test Suite - Robust with timeout handling.
"""

import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from langchain_huggingface import HuggingFaceEmbeddings
import chromadb
from chromadb.config import Settings
import httpx

MINIMAX_API_KEY = os.environ.get('MINIMAX_API_KEY', '') or (
    open('.env', 'r').read().split('MINIMAX_API_KEY=')[1].split('\n')[0]
)

emb = HuggingFaceEmbeddings(model_name='BAAI/bge-large-en-v1.5', model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True})
client = chromadb.PersistentClient(path='./chroma_db', settings=Settings(anonymized_telemetry=False))
collection = client.get_collection(name='local_rag_docs')

def search_chroma(query, k=3):
    query_emb = emb.embed_query(query)
    results = collection.query(query_embeddings=[query_emb], n_results=k, include=['documents', 'metadatas'])
    docs = []
    if results and results.get('documents'):
        for i, doc in enumerate(results['documents'][0]):
            meta = results.get('metadatas', [[{}]])[0][i] if results.get('metadatas') else {}
            docs.append({'content': doc, 'metadata': meta})
    return docs

def call_llm(prompt, timeout=45):
    try:
        resp = httpx.post(
            'https://api.minimax.io/v1/chat/completions',
            json={'model': 'MiniMax-M2.7', 'messages': [{'role': 'user', 'content': prompt}], 'stream': False},
            headers={'Authorization': f'Bearer {MINIMAX_API_KEY}', 'Content-Type': 'application/json'},
            timeout=timeout
        )
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content'], True
        else:
            return f"ERROR {resp.status_code}", False
    except Exception as e:
        return f"TIMEOUT/ERROR: {str(e)[:50]}", False

def truncate(t, n=200):
    return t[:n] + '...' if len(t) > n else t

print("""
╔══════════════════════════════════════════════════════════╗
║           RAG TEST SUITE - FAST EDITION                  ║
╚══════════════════════════════════════════════════════════╝
""")

print(f"Collection: {collection.count()} docs | Model: BGE-Large (1024 dims) | LLM: MiniMax-M2.7\n")

results = []

questions = [
    ("Matemáticas", "que es una derivada?", 3),
    ("Matemáticas", "explica el teorema fundamental del calculo", 3),
    ("Seguridad", "cuales son las mejores practicas de seguridad informatica?", 4),
    ("Arquitectura", "describe la arquitectura lambda y kappa", 4),
    ("Gestión", "que es la gestion del desempeño por competencia?", 3),
    ("Seguridad", "que es el malware y quais tipos existen?", 3),
    ("General", "cuales son los temas que tienes indexados?", 5),
]

print("=" * 70)
print("  PHASE 1: CATEGORY QUESTIONS")
print("=" * 70)

for cat, question, k in questions:
    print(f"\n[{cat}] {question}")
    print("-" * 60)

    t0 = time.time()
    docs = search_chroma(question, k=k)
    retrieval_time = time.time() - t0

    if not docs:
        print("  ⚠ No docs found")
        results.append({'cat': cat, 'q': question, 'status': 'no_docs'})
        continue

    context = '\n\n'.join([d['content'][:1500] for d in docs])
    prompt = f"Contexto:\n{context}\n\nPregunta: {question}\n\nResponde de forma directa, sin bloques de pensamiento. Usa SOLO la información del contexto. Si no hay suficiente información, di 'No tengo información suficiente'."

    t0 = time.time()
    answer, ok = call_llm(prompt, timeout=45)
    llm_time = time.time() - t0
    total_time = retrieval_time + llm_time

    if ok:
        print(f"  ✓ {len(docs)} docs | Retrieval: {retrieval_time:.2f}s | LLM: {llm_time:.2f}s | Total: {total_time:.2f}s")
        print(f"  Respuesta: {truncate(answer, 180)}")
        results.append({'cat': cat, 'q': question, 'status': 'ok', 'docs': len(docs), 'ret_time': retrieval_time, 'llm_time': llm_time, 'total': total_time})
    else:
        print(f"  ✗ Error: {answer}")
        results.append({'cat': cat, 'q': question, 'status': 'error', 'error': answer})

print("\n" + "=" * 70)
print("  PHASE 2: RAG ON vs OFF (quick comparison)")
print("=" * 70)

test_q = "que es el calculo diferencial?"

# RAG OFF
print(f"\nPregunta: {test_q}")
print("-" * 60)
print("  [RAG OFF] (sin documentos)...")
prompt_no_rag = f"Pregunta: {test_q}\n\nResponde de forma directa, sin bloques de pensamiento."
answer_no_rag, ok1 = call_llm(prompt_no_rag, timeout=30)

if ok1:
    print(f"  ✓ {truncate(answer_no_rag, 150)}")
else:
    print(f"  ✗ {answer_no_rag}")

# RAG ON
print("  [RAG ON] (con documentos)...")
docs = search_chroma(test_q, k=4)
context = '\n\n'.join([d['content'][:1500] for d in docs])
prompt_rag = f"Contexto:\n{context}\n\nPregunta: {test_q}\n\nResponde de forma directa, sin bloques de pensamiento. Usa SOLO la información del contexto."
answer_rag, ok2 = call_llm(prompt_rag, timeout=30)

if ok2:
    print(f"  ✓ {truncate(answer_rag, 150)}")
else:
    print(f"  ✗ {answer_rag}")

if ok1 and ok2:
    print(f"\n  📊 RAG OFF: {len(answer_no_rag)} chars | RAG ON: {len(answer_rag)} chars")

print("\n" + "=" * 70)
print("  PHASE 3: COMPARATIVE QUERIES (auto k=15)")
print("=" * 70)

comp_questions = [
    "cual es mas importante: seguridad o velocidad?",
    "diferencia entre arquitectura lambda y kappa",
]

for q in comp_questions:
    print(f"\nPregunta: {q}")
    print("-" * 60)

    is_comp = any(kw in q.lower() for kw in ['mas importante', 'mejor', 'diferencia', 'compar', 'vs'])
    k = 15 if is_comp else 5
    print(f"  Comparative: {is_comp} → k={k}")

    docs = search_chroma(q, k=k)
    context = '\n\n'.join([d['content'][:1500] for d in docs])
    prompt = f"Contexto:\n{context}\n\nPregunta: {q}\n\nResponde de forma directa, sin bloques de pensamiento. Usa SOLO la información del contexto."

    answer, ok = call_llm(prompt, timeout=45)
    if ok:
        print(f"  ✓ {truncate(answer, 180)}")
    else:
        print(f"  ✗ {answer}")

print("\n" + "=" * 70)
print("  PHASE 4: SUMMARY METRICS")
print("=" * 70)

ok_results = [r for r in results if r.get('status') == 'ok']
failed_results = [r for r in results if r.get('status') != 'ok']

print(f"\nTotal questions: {len(results)}")
print(f"  Successful: {len(ok_results)}")
print(f"  Failed: {len(failed_results)}")

if ok_results:
    avg_ret = sum(r['ret_time'] for r in ok_results) / len(ok_results)
    avg_llm = sum(r['llm_time'] for r in ok_results) / len(ok_results)
    avg_total = sum(r['total'] for r in ok_results) / len(ok_results)

    print(f"\nAverage retrieval time: {avg_ret:.2f}s")
    print(f"Average LLM time: {avg_llm:.2f}s")
    print(f"Average total time: {avg_total:.2f}s")

    print(f"\n{'Category':<15} {'Question':<45} {'Docs':<5} {'Total(s)'}")
    print("-" * 80)
    for r in ok_results:
        q_short = r['q'][:42] + '...' if len(r['q']) > 45 else r['q']
        print(f"{r['cat']:<15} {q_short:<45} {r['docs']:<5} {r['total']:.2f}")

print("""
╔══════════════════════════════════════════════════════════╗
║                     TEST COMPLETE                         ║
╚══════════════════════════════════════════════════════════╝
""")