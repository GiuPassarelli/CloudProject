# CloudProject

Para usar:

Instalar boto3 e paramiko

Instalar aws config e realizar o cofigure credentials

Assume-se que o elastic ip '3.219.122.232' está alocado em north virginia e o ip '18.188.197.225' em ohio

Run projeto.py para rodar

Após criada, entre na instância do auto-scale por ssh e rode um curl para o database albums com o elastic ip de north virginia, por exemplo:

$ curl -X GET http://3.219.122.232:5000/albums

Database usado: couchdb
