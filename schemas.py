from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TipoDocumento(str, Enum):
    CONTRATO_SOCIAL = "Contrato Social"
    ESTATUTO = "Estatuto Social"
    ATA_CONSTITUICAO = "Ata de Constituição"
    TERMO_POSSE_ADMINISTRADOR = "Termo de Posse de Administrador"
    ALTERACAO_CONTRATUAL = "Alteração Contratual"
    OUTRO = "Outro"


# Data models
class Empresa(BaseModel):
    nome: str
    cnpj: str | None = None
    resumo: str = Field(description="Resumo de informações da empresa")
    objeto_social: str | None = Field(None, description="Objeto social da empresa")


class Pessoa(BaseModel):
    nome: str
    cpf: str | None = None
    resumo: str = Field(description="Resumo de informações da pessoa")


class Documento(BaseModel):
    nome: str = Field(description="Nome do documento")
    resumo: str = Field(description="Resumo de informações do documento")
    tipo: TipoDocumento = Field(description="Tipo de documento")


class ResumoEnvolvidos(BaseModel):
    pessoas: list[Pessoa] = Field(description="Lista de pessoas mencionadas nos documentos")
    empresas: list[Empresa] = Field(description="Lista de empresas mencionadas nos documentos")
    documentos: list[Documento] = Field(description="Lista de documentos contidos no PDF")


class DocumentoConstituicao(BaseModel):
    """Detalhes do documento de constituição de pessoa jurídica"""
    nome: str = Field(description="Nome do documento de constituição de pessoa jurídica")
    tipo: TipoDocumento = Field(description="Tipo de documento (contrato social, ata, estatuto, etc)")
    resumo_detalhado: str = Field(description="Resumo detalhado do conteúdo")


class NoDocumentoConstituicao(BaseModel):
    """Quando não encontra documento de constituição de pessoa jurídica válido"""


# class AnaliseGestao(BaseModel):
#     """Análise de gestão da empresa"""
#     # empresa: Empresa = Field(description="Dados da empresa analisada")
#     # documentos_constituicao: list[DocumentoConstituicao] = Field(description="Documentos de constituição encontrados")
#     socios: Optional[list[Socio]] = Field(description="Sócios que respondem pela empresa")
#     clausulas: Optional[List[str]] = Field(
#         default=None,
#         description="Lista de cláusulas identificadas nos documentos de constituição que determinam quem pode assinar documentos"
#     )
#     socios_representantes: Optional[List[Socio]] = Field(
#         default=None,
#         description="Lista de sócios que têm poderes representativos"
    # )

class Socio(BaseModel):
    """Representa um sócio da empresa e suas informações."""
    nome: str = Field(description="Nome completo do sócio")
    empresa: str = Field(description="Nome da empresa na qual é sócio")
    eh_administrador: bool = Field(
        default=False,
        description="Indica se o sócio é oficialmente designado como administrador"
    )
    pode_assinar_documentos: bool = Field(
        default=False,
        description="Indica se o sócio tem autorização para assinar documentos em nome da empresa"
    )
    pode_assinar_procuracoes: bool = Field(
        default=False,
        description="Indica se o sócio tem autorização para assinar procurações em nome da empresa"
    )


class ClausulaRestritiva(BaseModel):
    """Representa uma cláusula restritiva sobre assinatura de documentos ou procurações."""
    tipo: str = Field(
        description="Tipo de restrição (ex: 'assinatura conjunta', 'limite de valor', 'aprovação prévia')"
    )
    descricao: str = Field(
        description="Descrição simplificada da restrição imposta pela cláusula"
    )


class AnalisePoderAssinatura(BaseModel):
    """Análise dos poderes de assinatura com base nos documentos de constituição."""
    
    empresa: Empresa = Field(description="Dados da empresa analisada")
    documentos_constituicao: list[DocumentoConstituicao] = Field(description="Documentos de constituição encontrados")    
    socios: List[Socio] = Field(
        description="Lista de todos os sócios identificados nos documentos"
    )
    
    socios_administradores: List[str] = Field(
        description="Lista de nomes dos sócios que são administradores oficiais"
    )
    
    socios_com_poder_assinatura: List[str] = Field(
        description="Lista de nomes dos sócios que podem assinar documentos e procurações"
    )
    
    possui_clausulas_restritivas: bool = Field(
        description="Indica se existem cláusulas que restringem ou condicionam os poderes de assinatura"
    )
    
    clausulas_restritivas: Optional[List[ClausulaRestritiva]] = Field(
        default=None,
        description="Lista de cláusulas restritivas identificadas, se houver"
    )
    
    requer_assinatura_conjunta: bool = Field(
        description="Indica se há exigência de assinatura conjunta para documentos ou procurações"
    )
    
    requer_revisao_manual: bool = Field(
        description="Indica se a análise deve ser complementada com revisão manual devido a restrições contratuais"
    )
    
    observacoes: Optional[str] = Field(
        default=None,
        description="Observações adicionais sobre a análise realizada"
    )



class AnaliseGestao(BaseModel):
    empresa: Empresa = Field(description="Dados da empresa analisada")
    documentos_constituicao: list[DocumentoConstituicao] = Field(default_factory=list, description="Documentos de constituição encontrados")
    socios_com_poder_assinatura: list[Socio] = Field(default_factory=list, description="Sócios com poder de assinatura de documentos e procurações representando a empresa")
    clausulas_restritivas: List[ClausulaRestritiva] = Field(default_factory=list, description="Lista de cláusulas restritivas identificadas, se houver")


class NoAnaliseGestao(BaseModel):
    """Quando não encontra documentos de constituição válidos"""


class ResultadoAnalise(BaseModel):
    sucesso: bool = True
    mensagem: str = ""
    empresa_presente: Optional[bool] = None
    possui_doc_constituicao: Optional[bool] = None
    analise: Optional[AnaliseGestao] = None
    # identificacao: Optional[ResumoEnvolvidos] = None

