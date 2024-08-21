from flask import Flask, request, jsonify
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.document_loaders import PDFPlumberLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import PromptTemplate

app = Flask(__name__)

# Definir o caminho da pasta para o armazenamento persistente
folder_path = "db"

# Inicializar o LLM Ollama apontando para o serviço interno do Docker
cached_llm = Ollama(model="llama3", base_url="http://ollama:11434")

# Configurar o embedding para o uso de vetores
embedding = FastEmbedEmbeddings()

# Configurar o separador de texto para dividir o conteúdo
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024, chunk_overlap=80, length_function=len, is_separator_regex=False
)

# Definir o prompt padrão para o assistente técnico
raw_prompt = PromptTemplate.from_template(
    """
    <s>[INST] you are a technical assistant good at searching documents. If you do not have an answer from the provided information say so. [/INST] </s>
    [INST] {input}
            Context: {context}
            Answer: 
    [/INST]
""")

# Endpoint para processar uma consulta simples de IA
@app.route("/ai", methods=["POST"])
def aiPost():
    print("Post /ai called")
    json_content = request.json
    query = json_content.get("query")

    print(f"query: {query}")

    # Invocar o modelo de LLM com a consulta
    response = cached_llm.invoke(query)

    print(response)

    response_answer = {"answer": response}
    return jsonify(response_answer)

# Endpoint para processar consultas PDF utilizando um vetor de armazenamento
@app.route("/ask_pdf", methods=["POST"])
def askPDFPost():
    print("Post /ask_pdf called")
    json_content = request.json
    query = json_content.get("query")

    print(f"query: {query}")

    # Carregar a loja de vetores para fazer a recuperação dos documentos
    print("Loading vector store")
    vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)

    print("creating chain")
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": 20,
            "score_threshold": 0.1,
        }
    )

    # Criar uma cadeia de documentos para processar a consulta
    document_chain = create_stuff_documents_chain(cached_llm, raw_prompt)
    chain = create_retrieval_chain(retriever, document_chain)

    # Invocar a cadeia de documentos com a consulta
    result = chain.invoke({"input": query})

    print(result)

    sources = []
    for doc in result["context"]:
        sources.append(
            {"source": doc.metadata["source"], "page_content": doc.page_content}
        )

    response_answer = {"answer": result["answer"], "sources": sources}
    return jsonify(response_answer)

# Endpoint para fazer o upload de arquivos PDF e processá-los em chunks
@app.route("/pdf", methods=["POST"])
def pdfPost():
    file = request.files["file"]
    file_name = file.filename
    save_file = "pdf/" + file_name
    file.save(save_file)
    print(f"filename: {file_name}")

    # Carregar e dividir o documento PDF em partes
    loader = PDFPlumberLoader(save_file)
    docs = loader.load_and_split()
    print(f"docs len={len(docs)}")

    chunks = text_splitter.split_documents(docs)
    print(f"chunks len={len(chunks)}")

    # Persistir os chunks no armazenamento de vetores
    vector_store = Chroma.from_documents(
        documents=chunks, embedding=embedding, persist_directory=folder_path
    )

    vector_store.persist()

    response = {
        "status": "Successfully Uploaded",
        "filename": file_name,
        "doc_len": len(docs),
        "chunks": len(chunks),
    }

    return jsonify(response)

# Função para iniciar o servidor Flask
def start_app():    
    app.run(host="0.0.0.0", port=8080, debug=True)


if __name__ == "__main__":
    start_app()
