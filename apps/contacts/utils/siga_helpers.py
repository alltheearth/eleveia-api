# apps/contacts/utils/siga_helpers.py

from typing import Tuple, Optional


def extrair_periodo(nome_turma: Optional[str]) -> Optional[str]:
    """
    Extrai período de strings como "8E - Tarde", "1A Manhã", etc.
    Retorna o valor como vier na string, sem normalização.

    Args:
        nome_turma: Nome da turma (pode ser None)

    Returns:
        String com período identificado ou None

    Examples:
        >>> extrair_periodo("8E - Tarde")
        'tarde'
        >>> extrair_periodo("1A Manhã")
        'manha'
        >>> extrair_periodo("3B")
        None
    """
    if not nome_turma:
        return None

    nome_lower = nome_turma.lower()

    if 'manhã' in nome_lower or 'manha' in nome_lower:
        return 'manha'
    elif 'tarde' in nome_lower:
        return 'tarde'
    elif 'noite' in nome_lower:
        return 'noite'
    elif 'integral' in nome_lower:
        return 'integral'
    else:
        return None


def mapear_status(situacao_aluno_turma: Optional[str]) -> str:
    """
    Mapeia situação do SIGA para status padronizado.

    Args:
        situacao_aluno_turma: Situação retornada pela API

    Returns:
        Status padronizado ('ativo', 'concluido', 'transferido', 'inativo')

    Examples:
        >>> mapear_status("Cursando")
        'ativo'
        >>> mapear_status("Transferido")
        'transferido'
        >>> mapear_status(None)
        'ativo'
    """
    if not situacao_aluno_turma:
        return 'ativo'

    SITUACAO_MAP = {
        'Cursando': 'ativo',
        'Concluído': 'concluido',
        'Concluido': 'concluido',
        'Transferido': 'transferido',
        'Desistente': 'inativo',
        'Trancado': 'inativo',
        'Cancelado': 'inativo',
    }

    return SITUACAO_MAP.get(situacao_aluno_turma, 'ativo')


def deduzir_parentesco(guardian_id: int, student: dict) -> Tuple[str, str]:
    """
    Deduz parentesco baseado nos IDs de vínculo.

    Args:
        guardian_id: ID do responsável
        student: Dicionário com dados do aluno

    Returns:
        Tupla (codigo, display) com parentesco

    Examples:
        >>> student = {'mae_id': 100, 'pai_id': 200}
        >>> deduzir_parentesco(100, student)
        ('mae', 'Mãe')
        >>> deduzir_parentesco(200, student)
        ('pai', 'Pai')
    """
    if guardian_id == student.get('mae_id'):
        return 'mae', 'Mãe'
    elif guardian_id == student.get('pai_id'):
        return 'pai', 'Pai'
    elif guardian_id == student.get('responsavel_id'):
        return 'responsavel_principal', 'Responsável Principal'
    elif guardian_id == student.get('responsavel_secundario_id'):
        return 'responsavel_secundario', 'Responsável Secundário'
    else:
        return 'outro', 'Outro Responsável'