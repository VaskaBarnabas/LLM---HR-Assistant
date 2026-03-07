import chromadb
from experiments.langchain.pdfToText import extract_pdf_text

chroma_client = chromadb.HttpClient(host="localhost", port=8000)

collection = chroma_client.get_or_create_collection(name="cv_collection")

cv1_text = extract_pdf_text("example1.pdf")
cv2_text = extract_pdf_text("example2.pdf")
cv3_text= extract_pdf_text("example3.pdf")
cv4_text = extract_pdf_text("example4.pdf")

collection.upsert(
    ids=["id1", "id2", "id3", "id4"],
    documents=[
        cv1_text,
        cv2_text,
        cv3_text,
        cv4_text
    ]
)

results = collection.query(
    query_texts=["JavaScript React HTML CSS frontend web development"],
    n_results=1
)

ids       = results["ids"][0]
distances = results["distances"][0]
documents = results["documents"][0]

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

for rank, (doc_id, distance, document) in enumerate(zip(ids, distances, documents), start=1):
    print(f"\n  #{rank}  ID: {doc_id}  |  Distance: {distance:.4f}")
    print("-" * 60)
    preview = document[:400].replace("\n", " ")
    print(f"  {preview}{'...' if len(document) > 400 else ''}")

print("\n" + "=" * 60)
print(f"  BEST MATCH: {ids[0]}")
print("=" * 60)