from dataclasses import dataclass
from datetime import datetime

@dataclass
class Imagem:
    """modelo para a tabela imagens"""
    id: int
    nome: str
    largura: int
    altura: int
    tipo: str               # 'referencia' ou 'teste'
    criado_em: datetime = None


@dataclass
class Fatia:
    """modelo para a tabela fatias (trecho horizontal da imagem)"""
    id: int
    imagem_id: int          # referencia a imagem
    thread_id: int          # índice da fatia (ordem vertical)
    y_inicio: int           # linha inicial
    y_fim: int              # linha final
    media_r: float          # média do canal vermelho
    media_g: float          # média do canal verde
    media_b: float          # média do canal azul


@dataclass
class Inspecao:
    """modelo para a tabela inspecoes"""
    id: int
    imagem_referencia_id: int
    imagem_teste_id: int
    percentual_defeito: float
    status: str             # 'aprovado' ou 'reprovado'
    criado_em: datetime = None