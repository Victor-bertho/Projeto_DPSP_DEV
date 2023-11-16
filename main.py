from fastapi import FastAPI, HTTPException, status
from typing import List, Dict
from datetime import datetime, time  # Importação correta aqui
from app.models import Agendamento, AgendamentoRequest, Status, AgendamentosRequest, Usuario, UsuarioUpdate
from app.database import db
from app.utils import is_horario_disponivel, get_horarios_disponiveis, find_usuario_by_email, write_data, read_data,find_usuario_by_id, find_usuario_by_email_multi
from uuid import uuid4

app = FastAPI()
FILE_PATH = 'usuarios_farmacia.json'

@app.put("/agendamentos/{idAgendamento}", response_model=Agendamento)
async def atualizar_agendamento(idAgendamento: str, agendamento_update: AgendamentoRequest):
    # Encontra o agendamento existente
    agendamento = next((ag for ag in db if ag.idAgendamento == idAgendamento), None)
    if agendamento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado")

    # Verifica se o horário é cheio e dentro do horário comercial
    dataHora = agendamento_update.dataHora
    if dataHora.minute != 0 or dataHora.second != 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Agendamentos só podem ser marcados em horários cheios (ex: 10:00, 11:00)."
        )
    if not (time(9, 0) <= dataHora.time() <= time(17, 0)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Agendamentos devem ser dentro do horário comercial (9h às 17h)."
        )

    # Verifica se o novo horário está disponível
    if not is_horario_disponivel(dataHora, exclude_id=idAgendamento):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este horário está indisponível."
        )

    # Atualiza o agendamento com os novos detalhes
    agendamento.idUsuario = agendamento_update.idUsuario
    agendamento.servico = agendamento_update.servico
    agendamento.dataHora = dataHora
    # O status não é alterado pelo PUT
    return agendamento

@app.post("/agendamentos/", response_model=Agendamento)
async def criar_agendamento(agendamento_request: AgendamentoRequest):
    dataHora = agendamento_request.dataHora
    if dataHora < datetime.now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='A data e hora do agendamento devem ser futuras.')
    if not (time(9, 0) <= dataHora.time() <= time(17, 0)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Agendamentos devem ser dentro do horário comercial (9h às 17h).')
    if dataHora.minute != 0 or dataHora.second != 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Agendamentos só podem ser marcados em horários cheios (ex: 10:00, 11:00).')
    
    # Verifica se o horário desejado já está ocupado
    if not is_horario_disponivel(dataHora):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este horário já está reservado.")

    # Verifica se o usuário existe
    usuario = find_usuario_by_id(agendamento_request.idUsuario)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Usuário não encontrado.')

    id_agendamento = str(uuid4())
    novo_agendamento = Agendamento(
        idAgendamento=id_agendamento,
        idUsuario=usuario['nome'],  # Supondo que o idUsuario é o nome do usuário
        servico=agendamento_request.servico,
        dataHora=dataHora,
        status='ATIVO'  # Supondo que você queira definir o status como 'ATIVO'
    )
    db.append(novo_agendamento)
    return novo_agendamento

@app.get("/agendamentos/todos", response_model=List[Agendamento])
async def listar_agendamentos():
    return db

@app.get("/agendamentos/{idAgendamento}", response_model=Agendamento)
async def get_agendamento(idAgendamento: str):
    agendamento = next((ag for ag in db if ag.idAgendamento == idAgendamento), None)
    if agendamento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado")
    return agendamento

@app.delete("/agendamentos/{idAgendamento}", response_model=dict)
async def cancelar_agendamento(idAgendamento: str):
    agendamento = next((ag for ag in db if ag.idAgendamento == idAgendamento and ag.status == Status.ATIVO), None)
    if agendamento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado ou já cancelado.")
    agendamento.status = Status.CANCELADO
    return {"message": f"Agendamento com ID {idAgendamento} cancelado com sucesso."}


'''@app.post("/agendamentos/multiple/", response_model=List[Agendamento])
async def criar_multiplos_agendamentos(agendamentos_request: AgendamentosRequest):
    novos_agendamentos = []
    for agendamento_req in agendamentos_request.agendamentos:
        if not is_horario_disponivel(agendamento_req.dataHora):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Horário {agendamento_req.dataHora} está indisponível."
            )
        novo_agendamento = Agendamento(
            idUsuario=agendamento_req.idUsuario,
            servico=agendamento_req.servico,
            dataHora=agendamento_req.dataHora
        )
        db.append(novo_agendamento)
        novos_agendamentos.append(novo_agendamento)
    return novos_agendamentos'''

@app.post("/usuarios/", response_model=Usuario)
async def create_usuario(usuario: Usuario):
    usuarios = read_data()
    if find_usuario_by_email(usuario.email):
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    usuarios.append(usuario.dict(by_alias=True))
    write_data(usuarios)
    return usuario

@app.get("/usuarios/", response_model=List[Usuario])
async def read_usuarios():
    return read_data()

@app.get("/usuarios/{usuario_id}", response_model=Usuario)
async def read_usuario(usuario_id: str):
    usuarios = read_data()
    usuario = next((usuario for usuario in usuarios if usuario['id'] == usuario_id), None)
    if usuario:
        return usuario
    raise HTTPException(status_code=404, detail="Usuario não encontrado.")

@app.put("/usuarios/{usuario_id}", response_model=Usuario)
async def update_usuario(usuario_id: str, usuario_update: UsuarioUpdate):
    usuarios = read_data()
    usuario_index = next((index for index, u in enumerate(usuarios) if u['id'] == usuario_id), None)
    if usuario_index is None:
        raise HTTPException(status_code=404, detail="Usuario não encontrado.")

    if usuario_update.email and usuario_update.email != usuarios[usuario_index]['email']:
        if find_usuario_by_email(usuario_update.email):
            raise HTTPException(status_code=400, detail="E-mail já cadastrado.")

    if usuario_update.nome:
        usuarios[usuario_index]['nome'] = usuario_update.nome
    if usuario_update.email:
        usuarios[usuario_index]['email'] = usuario_update.email

    write_data(usuarios)
    return usuarios[usuario_index]

@app.delete("/usuarios/{usuario_id}")
async def delete_usuario(usuario_id: str):
    usuarios = read_data()
    usuario = next((usuario for usuario in usuarios if usuario['id'] == usuario_id), None)
    if usuario:
        usuarios = [u for u in usuarios if u['id'] != usuario_id]
        write_data(usuarios)
        return {"message": f"Usuario com ID {usuario_id} deletado com sucesso."}
    raise HTTPException(status_code=404, detail="Usuario não encontrado.")

@app.post("/usuarios/multiplos/", status_code=201)
async def create_multiple_usuarios(usuarios: List[Usuario]):
    existing_usuarios = read_data()
    new_usuarios_data = []

    for usuario in usuarios:
        if find_usuario_by_email_multi(usuario.email, existing_usuarios):
            raise HTTPException(
                status_code=400, 
                detail=f"O e-mail {usuario.email} já está cadastrado."
            )
        usuario.id = str(uuid4())
        new_usuarios_data.append(usuario.dict(by_alias=True))

    existing_usuarios.extend(new_usuarios_data)
    write_data(existing_usuarios)
    
    return new_usuarios_data