import chromadb
from experiments.langchain.pdfToText import extract_pdf_text

chroma_client = chromadb.HttpClient(host="localhost", port=8000)

collection = chroma_client.get_or_create_collection(name="cv_collection")

cv1_text = extract_pdf_text("example1.pdf")
cv2_text = extract_pdf_text("example2.pdf")
cv3_text= extract_pdf_text("example3.pdf")

collection.add(
    ids=["id1", "id2", "id3"],
    documents=[
        cv1_text,
        cv2_text,
        cv3_text
    ]
)

results = collection.query(
    query_texts=["Find the best candidate for Java developer"], # Chroma will embed this for you
    n_results=3 # how many results to return
)

#print(results)
doc_id   = results["ids"][0][0]
distance = results["distances"][0][0]
document = results["documents"][0][0]

print("\n" + "=" * 60)
print("  BEST MATCH")
print("=" * 60)
print(f"  ID: {doc_id}  |  Distance: {distance:.4f}")
print("-" * 60)
preview = document[:500].replace("\n", " ")
print(f"  {preview}{'...' if len(document) > 500 else ''}")
print("=" * 60)