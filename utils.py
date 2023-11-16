from .models import Status
from .database import db
from datetime import datetime
from typing import List, Dict
import json


FILE_PATH = 'usuarios_farmacia.json'

def is_horario_disponivel(desired_time: datetime, exclude_id: str = None) -> bool:
    return all(desired_time != agendamento.dataHora or agendamento.idAgendamento == exclude_id
               for agendamento in db if agendamento.status == Status.ATIVO)


def get_horarios_disponiveis(data: datetime.date) -> List[str]:
    horarios_disponiveis = []
    horario_inicio = datetime.datetime.combine(data, datetime.time(9, 0))
    horario_fim = datetime.datetime.combine(data, datetime.time(17, 0))

#############usuarios##############                                          
    
def read_data() -> List[Dict]:
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def write_data(usuarios: List[Dict]):
    with open(FILE_PATH, 'w') as file:
        json.dump(usuarios, file, default=str, ensure_ascii=False, indent=4)

def find_usuario_by_id(usuario_id: str) -> Dict:
    usuarios = read_data()
    return next((usuario for usuario in usuarios if usuario['id'] == usuario_id), None)

def find_usuario_by_email(email: str):
    usuarios = read_data()
    return next((usuario for usuario in usuarios if usuario['email'] == email), None)

def find_usuario_by_email_multi(email: str, usuarios: List[dict]) -> dict:
    return next((usuario for usuario in usuarios if usuario['email'] == email), None)