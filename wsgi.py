"""
wsgi.py — Ponto de entrada para o PythonAnywhere

O PythonAnywhere usa este arquivo para iniciar a aplicação.
Não é necessário rodar app.py diretamente lá.

Configure no painel do PythonAnywhere:
  Source code:   /home/SEU_USUARIO/controle_financeiro
  WSGI file:     aponte para este arquivo
  Working dir:   /home/SEU_USUARIO/controle_financeiro
"""

import sys
import os

# Adiciona a pasta do projeto ao PATH do Python
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Inicializa o banco de dados (cria tabelas se não existirem)
import database as db
db.iniciar_banco()

# Importa a aplicação Flask
from app import app as application  # noqa
