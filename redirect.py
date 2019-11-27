import requests, os, json
from flask import Flask, request
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)
api = Api(app)

username = 'GiuPassarelli'
senha = 'banana'
ip = os.environ['IPDB']
porta = '5000'


requests.put('http://%s:%s@%s:%s/albums' % (username, senha, ip, porta))
res = requests.get('http://%s:%s/_uuids' % (ip, porta))
uuid = res.json()['uuids'][0]
dados_a_serem_salvos = '{"Nome":"Carlos","Instrumento":"Guitarra"}'

res = requests.put('http://%s:%s@%s:%s/albums/%s' % (username, senha, ip, porta, uuid), json=dados_a_serem_salvos)

dados_a_serem_salvos = ['{"Nome":"Pedro","Instrumento":"Guitarra"}','{"Nome":"Magda","Instrumento":"Piano"}','{"Nome":"Jubileu","Instrumento":"Saxofone"}']

for i in dados_a_serem_salvos:
    
    res = requests.get('http://%s:%s/_uuids' % (ip, porta))
    # Salvando o ID gerado
    uuid = res.json()['uuids'][0]
    # Salvando dados
    res = requests.put('http://%s:%s@%s:%s/albums/%s' % (username,senha,ip,porta,uuid),data=i)

@app.route('/healthcheck')
def Healthcheck():
    return '', 200

@app.route('/Tarefa', methods=['GET'])
def get_tarefas():
    res = requests.get('http://%s:%s/albums/_all_docs' % (ip,porta))
    res = res.json()
    new_json = {}
    for i in res:
        res2 = requests.get('http://%s:%s/albums/_all_docs/%s' % (ip,porta,i["id"]))
        temp_dict = res2.json()
        del temp_dict["_id"]
        del temp_dict["_rev"]
        new_json[i["id"]] = temp_dict
    print(new_json)

    return new_json

@app.route('/Tarefa', methods=['POST'])
def post_tarefas():
    new_tarefa = request.form.to_dict(flat=False)
    res = requests.get('http://%s:%s/_uuids' % (ip, porta))
    uuid = res.json()['uuids'][0]
    res = requests.put('http://%s:%s@%s:%s/albums/%s' % (username, senha, ip, porta, uuid), json=new_tarefa)
    return res.json(), 201

@app.route('/Tarefa/<int:id>', methods=['GET'])
def get_tarefa():
    res = requests.get('http://%s:%s/albums/_all_docs/%s' % (ip,porta,id))
    return res.json()

@app.route('/Tarefa/<int:id>', methods=['PUT'])
def put_tarefa():
    new_tarefa = request.form.to_dict(flat=False)
    res = requests.get('http://%s:%s/albums/%s' % (ip, porta, id))
    rev = res.json()['_rev']
    new_tarefa["_rev"] = rev
    res = requests.put('http://%s:%s@%s:%s/albums/%s' % (username,senha,ip,porta,id), json=new_tarefa)
    return res.json(), 201

@app.route('/Tarefa/<int:id>', methods=['DELETE'])
def del_tarefa():
    res = requests.get('http://%s:%s/albums/%s' % (ip, porta, id))
    rev = res.json()['rev']
    res = requests.delete('http://%s:%s@%s:%s/albums/%s?rev=%s' % (username,senha,ip,porta,id,rev))
    return res.json(), 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=False)