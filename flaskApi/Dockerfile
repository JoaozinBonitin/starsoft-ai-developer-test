FROM python:3.10-slim

# Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar o arquivo de requisitos para o contêiner
COPY requirements.txt .

# Instalação de Todas as dependências necessarias para rodar o projeto
RUN pip install flask
RUN pip install -U langchain-community
RUN pip install cmake
RUN apt-get update && apt-get install -y build-essential  
RUN pip install fastembed  
RUN pip install pdfplumber
RUN pip install chromadb
RUN pip install -U langchain-chroma


# Copiar o código da aplicação para o contêiner
COPY . /app

# Expor a porta usada pelo Flask
EXPOSE 8080

# Comando para rodar a aplicação Flask
CMD ["python", "app.py"]