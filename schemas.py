from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class TipoDocumento(str, Enum):
    CONTRATO_SOCIAL = "Contrato Social"
    ESTATUTO = "Estatuto Social"
    ATA_CONSTITUICAO = "Ata de Constituição"
    TERMO_POSSE_ADMINISTRADOR = "Termo de Posse de Administrador"
    ALTERACAO_CONTRATUAL = "Alteração Contratual"
    PROCURACAO = "Procuração"
    ATA_ASSEMBLEIA = "Ata de Assembleia"
    OUTRO = "Outro"


class TipoSocietario(str, Enum):
    LTDA = "Sociedade Limitada"
    SA = "Sociedade Anônima"
    EIRELI = "Empresa Individual de Responsabilidade Limitada"
    MEI = "Microempreendedor Individual"
    SLU = "Sociedade Limitada Unipessoal"
    OUTRO = "Outro"


class FormaAdministracao(str, Enum):
    ADMINISTRADOR_UNICO = "Administrador Único"
    ADMINISTRACAO_CONJUNTA = "Administração Conjunta"
    DIRETORIA = "Diretoria"
    CONSELHO_ADMINISTRACAO = "Conselho de Administração"
    OUTRO = "Outro"


# Data models
class Empresa(BaseModel):
    nome: str
    cnpj: str | None = None
    tipo_societario: TipoSocietario | None = None
    data_constituicao: str | None = None
    resumo: str = Field(description="Resumo de informações da empresa")
    objeto_social: str | None = Field(None, description="Objeto social da empresa")
    ramo_atuacao: str | None = Field(None, description="Ramo de atuação da empresa")


class Pessoa(BaseModel):
    nome: str
    cpf: str | None = None
    resumo: str = Field(description="Resumo de informações da pessoa")


class Documento(BaseModel):
    nome: str = Field(description="Nome do documento")
    resumo: str = Field(description="Resumo de informações do documento")
    tipo: TipoDocumento = Field(description="Tipo de documento")
    data: str | None = Field(None, description="Data do documento")
    numero_registro: str | None = Field(None, description="Número de registro do documento")
    orgao_registro: str | None = Field(None, description="Órgão de registro do documento")


class ResumoEnvolvidos(BaseModel):
    pessoas: list[Pessoa] = Field(
        description="Lista de pessoas mencionadas nos documentos"
    )
    empresas: list[Empresa] = Field(
        description="Lista de empresas mencionadas nos documentos"
    )
    documentos: list[Documento] = Field(
        description="Lista de documentos contidos no PDF"
    )


class DocumentoConstituicao(BaseModel):
    """Detalhes do documento de constituição de pessoa jurídica"""
    nome: str = Field(description="Nome do documento de constituição de pessoa jurídica")
    tipo: TipoDocumento = Field(description="Tipo de documento (contrato social, ata, estatuto, etc)")
    data: str | None = Field(None, description="Data do documento")
    numero_registro: str | None = Field(None, description="Número de registro do documento")
    orgao_registro: str | None = Field(None, description="Órgão de registro do documento")
    resumo_detalhado: str = Field(description="Resumo detalhado do conteúdo")


class NoDocumentoConstituicao(BaseModel):
    """Quando não encontra documento de constituição de pessoa jurídica válido"""
    pass


class Socio(BaseModel):
    """Representa um sócio da empresa e suas informações."""
    nome: str = Field(description="Nome completo do sócio")
    empresa: str = Field(description="Nome da empresa na qual é sócio")
    participacao: str | None = Field(None, description="Percentual ou valor da participação societária")
    cargo: str | None = Field(None, description="Cargo ou função na administração da empresa")
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
    # texto_original: str | None = Field(
    #     None,
    #     description="Texto original da cláusula conforme consta no documento"
    # )
    aplicavel_transferencia_veicular: bool = Field(
        default=False,
        description="Indica se a cláusula se aplica especificamente a transferências veiculares"
    )


class AnaliseGestao(BaseModel):
    """Análise completa da gestão e representação da empresa"""
    
    empresa: Empresa = Field(
        description="Dados completos da empresa analisada, incluindo nome, CNPJ, tipo societário, data de constituição, objeto social e ramo de atuação"
    )
    
    tipo_societario: TipoSocietario | None = Field(
        None, 
        description="Tipo societário da empresa (Ltda, S.A., EIRELI, etc.) conforme consta nos documentos de constituição"
    )
    
    forma_administracao: FormaAdministracao | None = Field(
        None, 
        description="Forma de administração da empresa (administrador único, administração conjunta, diretoria, etc.)"
    )
    
    socios_com_poder_assinatura: list[Socio] = Field(
        default_factory=list, 
        description="Lista de sócios que podem assinar documentos e procurações em nome da empresa"
    )
    
    clausulas_restritivas: List[ClausulaRestritiva] = Field(
        default_factory=list, 
        description="Lista de cláusulas que estabelecem condições para representação da empresa"
    )
    
    analise_transferencia_veicular: str | None = Field(
        None, 
        description="Análise específica sobre quem pode representar a empresa para transferência veicular"
    )


class NoAnaliseGestao(BaseModel):
    """Quando não é possível realizar a análise de gestão"""
    pass


class ConclusaoAnalise(BaseModel):
    """Conclusão da análise dos documentos de constituição"""
    
    socios_com_poder_assinatura: list[Socio] = Field(
        default_factory=list, 
        description="Lista de sócios que podem assinar documentos e procurações em nome da empresa, com detalhes sobre seus poderes específicos"
    )
    
    clausulas_restritivas: List[ClausulaRestritiva] = Field(
        default_factory=list, 
        description="Lista de cláusulas que estabelecem condições para representação da empresa"
    )
    
    requer_analise_especializada: bool = Field(
        default=False, 
        description="Indica se a análise requer revisão por profissional especializado devido a cláusulas complexas, ambiguidades ou informações insuficientes"
    )
    
    justificativa_analise_especializada: str | None = Field(
        None,
        description="Justificativa detalhada para a necessidade de análise por profissional especializado, quando aplicável"
    )
   
    conclusao: str = Field(
        description="Resumo objetivo de quem pode representar a empresa e quais restrições são aplicáveis"
    )


class ResultadoAnalise(BaseModel):
    """Resultado final da análise de documentos"""
    sucesso: bool = True
    mensagem: str = ""
    conclusao: ConclusaoAnalise | None = None
