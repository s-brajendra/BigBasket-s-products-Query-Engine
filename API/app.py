import pickle
from sentence_transformers import SentenceTransformer
from flask import Flask,request,jsonify
from flask_cors import CORS
from flask_cors import cross_origin


BERT_MODEL_PATH = "./data/bert-question-answering.pkl"
ENC_PATH  = "./data/encodermodel.pkl"
QDRANT_PATH  = "./data/qdrant_space_client.pkl"


with open(BERT_MODEL_PATH, 'rb') as file:
    bert = pickle.load(file)
with open(QDRANT_PATH, 'rb') as file:
    qdrant_client = pickle.load(file)
with open(ENC_PATH, 'rb') as file:
    st_encoder = pickle.load(file)

collection_name = "qdrant-space"
def find_close_contexts(question: str, top_k: int) -> list[str]:
    """
    will return contexts contexts close to query

    Args:
        question (str): What do we want to know?
        top_k (int): top k results will be added

    Returns:
        context (List[str]):
    """
    try:
        encoded_query = st_encoder.encode(question).tolist()
        result = qdrant_client.search(
            collection_name=collection_name,
            query_vector=encoded_query,
            limit=top_k,
        )  # search qdrant collection for context passage with the answer

        context = [
            [context.payload["product"], context.payload["story"]] for context in result
        ]
        return context
    except Exception as e:
        print({e})

def tell_me(question: str, context: list[str]):
    """
    Extract the answer from the context for a given question

    Args:
        question (str): _description_
        context (list[str]): _description_
    """
    results = []
    for c in context:
        answer = bert(question=question, context=c[1] )
        answer["product"] = c[0]
        results.append(answer)
        print()

    sorted_result = sorted(results, key=lambda x: x["score"], reverse=True)
    for i in range(len(sorted_result)):
        _out = sorted_result[i]["answer"]
        _prod = sorted_result[i]["product"]
        _sco = sorted_result[i]["score"]
#         print(f"{i+1}", end=" ")
        print(f"QUERY INPUT: {question}")
        print(f"OUTPUT: {_out} \nPREDICTION SCORE {_sco}\n\nReferred Product: {_prod}\n\n")
        return question,_out,_sco,_prod



app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})


# by default get request
@app.route('/')
def home():
    return {
        "api_name": "BigBasket-s-products-Query-Engine"
    }

@app.route('/test', methods=['POST'])
@cross_origin(origin='http://localhost:3000', headers=['Content-Type', 'Authorization'])
def test():
    data = request.get_json()

    _ques  = data["question"]
    c = find_close_contexts(_ques, top_k=1)
    _ques, _out, _sco, _prod = tell_me(_ques, c)

    result = {
        "_ques": _ques,
        "_out":_out,
        "_sco":_sco,
        "_prod":_prod
    }

    return {
        "type":"output",
        "status":200,
        "payload": result,
     }

if __name__ == '__main__':
    app.run(debug=True)