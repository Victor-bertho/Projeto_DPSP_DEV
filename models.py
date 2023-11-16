from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, date
from enum import Enum
from uuid import uuid4
from typing import List, Optional


class Status(str, Enum):
    ATIVO = "ATIVO"
    CANCELADO = "CANCELADO"

class Agendamento(BaseModel):
    idAgendamento: str = Field(default_factory=lambda: str(uuid4()))
    idUsuario: str
    servico: str
    dataHora: datetime
    status: Status = Status.ATIVO

class AgendamentoRequest(BaseModel):
    idUsuario: str
    servico: str
    dataHora: datetime

class AgendamentosRequest(BaseModel):
    agendamentos: List[AgendamentoRequest]


#usuarios
class Usuario(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    nome: str
    email: EmailStr
    dataNascimento: date

class UsuarioUpdate(BaseModel):
    nome: Optional[str]
    email: Optional[EmailStr]
