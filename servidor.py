import requests, os, json
from flask import Flask, request
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)
api = Api(app)

username = 'GiuPassarelli'
senha = 'banana'
ip = os.environ['IPNEXT']
porta = '5000'

@app.route('/healthcheck')
def Healthcheck():
    return '', 200

@app.route('/Tarefa', methods=['GET'])
def get_tarefas():
    res = requests.get('http://%s:%s/albums' % (ip,porta))
    return res.json()

@app.route('/Tarefa', methods=['POST'])
def post_tarefas():
    new_tarefa = request.form.to_dict(flat=False)
    res = requests.put('http://%s:%s@%s:%s/albums' % (username, senha, ip, porta), json=new_tarefa)
    return res.json(), 201

@app.route('/Tarefa/<int:id>', methods=['GET'])
def get_tarefa():
    res = requests.get('http://%s:%s/albums/%s' % (ip,porta,id))
    return res.json()

@app.route('/Tarefa/<int:id>', methods=['PUT'])
def put_tarefa():
    new_tarefa = request.form.to_dict(flat=False)
    res = requests.put('http://%s:%s@%s:%s/albums/%s' % (username,senha,ip,porta,id), json=new_tarefa)
    return res.json(), 201

@app.route('/Tarefa/<int:id>', methods=['DELETE'])
def del_tarefa():
    res = requests.delete('http://%s:%s@%s:%s/albums/%s' % (username,senha,ip,porta,id))
    return res.json(), 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=False)