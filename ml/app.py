import re
import json
import requests

import torch
from flask import Flask, request, Response
from flask_cors import CORS, cross_origin
from annoy import AnnoyIndex
from llama_index import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.llms import HuggingFaceLLM
from llama_index.text_splitter import TokenTextSplitter
from llama_index.node_parser import SimpleNodeParser
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, PeftConfig

from open_ai import get_description
from get_embedding import Embedder


EMBED_MODEL_NAME = "cointegrated/LaBSE-en-ru"
LLM_MODEL_NAME = "IlyaGusev/saiga2_7b_lora"
TOP_K = 5
PROMT_WRAPPER = "Ответь на вопрос: {query_str}"
SYSTEM_PROMT = "Ты умный ассистент которого зовут Хьюстон. Ты любишь отвечать на вопросы пользователей."
SKILL_URL = 'http://45.80.71.85:8000/api/v1/skill/'


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
embedder = Embedder("sentence-transformers/LaBSE").to(device)
u = AnnoyIndex(768, 'angular')
u.load('AnnoyIndex_128.ann')
with open("id2name.json", "r") as file:
    id2name = json.load(file)
with open("id2link.json", "r") as file:
    id2link = json.load(file)


def create_one(data: dict) -> Response:
    '''
    Создает запись в бд

    input: data: dict
    output: response: Response
    '''
    response = requests.post(SKILL_URL, json=data)

    return response


def read(skills_names: list) -> Response:
    '''
    Чтение из бд

    input: data: dict
    output: response: Response
    '''
    params = '&'.join([f'name={name}' for name in skills_names])
    response = requests.get(SKILL_URL + '?' + params)

    return response


def node_processor(nodes):
    for node in nodes:
        node.text = re.sub("\\n", " ", node.text)
        node.text = re.sub(" +", " ", node.text)

    return nodes


def load_model():
    docs = SimpleDirectoryReader(input_dir='data_txt').load_data()
    text_splitter = TokenTextSplitter(
        separator="\n\n", chunk_size=512, chunk_overlap=128)
    parser = SimpleNodeParser.from_defaults(text_splitter=text_splitter)
    nodes = parser.get_nodes_from_documents(docs)
    nodes = node_processor(nodes)

    config = PeftConfig.from_pretrained(LLM_MODEL_NAME)
    llm = AutoModelForCausalLM.from_pretrained(
        config.base_model_name_or_path,
        torch_dtype=torch.float16,
        load_in_8bit=False,
        device_map="auto"
    )
    llm = PeftModel.from_pretrained(
        llm, LLM_MODEL_NAME, torch_dtype=torch.float16)
    tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME, use_fast=False)
    llm = HuggingFaceLLM(
        model=llm,
        tokenizer=tokenizer,
        context_window=4096,
        max_new_tokens=256,
        generate_kwargs={"temperature": 0.0, "do_sample": False},
        query_wrapper_prompt=PROMT_WRAPPER,
        system_prompt=SYSTEM_PROMT,
        device_map="auto",
        tokenizer_kwargs={"max_length": 4096},
        model_kwargs={"torch_dtype": torch.float16}
    )
    service_context = ServiceContext.from_defaults(
        chunk_size=256, llm=llm, embed_model=f"local:{EMBED_MODEL_NAME}")
    index = VectorStoreIndex(nodes=nodes, service_context=service_context)
    query_engine = index.as_query_engine(similarity_top_k=TOP_K)

    return query_engine


query_engine = load_model()


def get_response(query):
    res = query_engine.query(query)

    return res.response.strip()


@app.route("/", methods=["GET"])
def test() -> dict:
    '''
    Проводит тест

    input: None
    output: dict
    '''
    return {"Status": "Ok"}


@app.route("/get_answer", methods=["POST"], endpoint='get_answer')
@cross_origin()
def get_answer() -> dict:
    '''
    Возвращает ответ

    input: None
    ouput: Response
    '''
    query = json.loads(request.data)["query"]
    response = get_response(query)

    return {"response": response}


@app.route("/get_keyword_desc", methods=["POST"], endpoint='get_keyword_desc')
@cross_origin()
def get_keywords_desc() -> Response:
    '''
    input: None
    output: Response
    '''
    result = []
    data = json.loads(request.data)
    keyword = data["keyword"]
    num_courses = data["num_courses"]
    db_response = read([keyword]).json()
    if db_response:
        descs_emb = db_response[0]["vector"]
    else:
        keyword_desc = get_description(keyword)
        embedding = embedder.get_embedding(
            list(keyword_desc.strip()))[0].tolist()
        descs_emb = embedding
        create_one({"name": keyword, "vector": descs_emb})

    search_ids = u.get_nns_by_vector(descs_emb, num_courses)
    courses = [(id2name[str(id)], id2link[str(id)]) for id in search_ids]

    return Response(json.dumps({"keyword": courses}, ensure_ascii=False).encode('utf8'), mimetype='application/json')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
