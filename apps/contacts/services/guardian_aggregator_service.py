# apps/contacts/services/guardian_aggregator_service.py

"""
Serviço de agregação de dados do SIGA.

Responsabilidade ÚNICA:
- Fazer JOIN entre as 3 APIs do SIGA
- Produzir dicts RICOS com todos os campos disponíveis
- NÃO decide o que mostrar (serializers fazem isso)
- NÃO busca boletos (InvoiceService faz isso)
- NÃO calcula resumos (GuardianService faz isso)
"""

import logging
from typing import List, Dict
from collections import defaultdict
from ..utils.siga_helpers import extrair_periodo, mapear_status

logger = logging.getLogger(__name__)

# Mapeamento de estado civil (SIGA retorna código numérico)
ESTADO_CIVIL_MAP = {
    '0': 'Solteiro(a)',
    '1': 'Casado(a)',
    '2': 'Divorciado(a)',
    '3': 'Viúvo(a)',
    '4': 'Separado(a)',
    '5': 'União Estável',
}


class GuardianAggregatorService:
    """
    Faz JOIN entre as 3 APIs e produz dicts completos.

    Fluxo:
    1. Mescla dados acadêmicos nos alunos (students_relations + students_academic)
    2. Agrupa alunos por responsável (via mae_id, pai_id, etc.)
    3. Constrói dict completo de cada responsável com todos os campos
    """

    def build_guardians_response(
        self,
        guardians: List[Dict],
        students_relations: List[Dict],
        students_academic: List[Dict],
    ) -> List[Dict]:
        """
        Constrói resposta completa com responsáveis e filhos.

        Args:
            guardians: API lista_responsaveis_dados_sensiveis
            students_relations: API lista_alunos_dados_sensiveis
            students_academic: API acesso/alunos

        Returns:
            Lista de dicts formatados (um por responsável)
        """
        # 1. JOIN: alunos + dados acadêmicos
        students_full = self._merge_student_data(
            students_relations, students_academic
        )

        # 2. Agrupar alunos por responsável
        guardian_students_map = self._group_students_by_guardian(students_full)

        # 3. Construir resposta final
        result = []
        for guardian in guardians:
            guardian_id = guardian['id']
            children = guardian_students_map.get(guardian_id, [])
            guardian_dict = self._build_guardian_dict(guardian, children)
            result.append(guardian_dict)

        logger.info(f"Aggregated {len(result)} guardians")
        return result

    # -----------------------------------------------------------------
    # MERGE: alunos + dados acadêmicos
    # -----------------------------------------------------------------

    def _merge_student_data(
        self,
        students_relations: List[Dict],
        students_academic: List[Dict],
    ) -> List[Dict]:
        """
        JOIN entre lista_alunos_dados_sensiveis e acesso/alunos.
        Usa id_aluno como chave de junção.
        """
        # Índice O(1) para dados acadêmicos
        academic_by_id = {}
        for s in students_academic:
            sid = s.get('id_aluno')
            if sid:
                academic_by_id[sid] = s

        merged = []
        for student_rel in students_relations:
            student_id = student_rel['id']
            academic = academic_by_id.get(student_id, {})

            merged.append({
                # Dados de relacionamento (lista_alunos_dados_sensiveis)
                **student_rel,
                # Dados acadêmicos (acesso/alunos) — adicionados
                '_turma': academic.get('nome_curso'),
                '_serie': academic.get('nome_serie'),
                '_turma_nome': academic.get('nome_turma'),
                '_situacao': academic.get('situacao_aluno_turma'),
            })

        logger.debug(f"Merged {len(merged)} students with academic data")
        return merged

    # -----------------------------------------------------------------
    # AGRUPAMENTO: alunos por responsável
    # -----------------------------------------------------------------

    def _group_students_by_guardian(
        self, students: List[Dict]
    ) -> Dict[int, List[Dict]]:
        """
        Agrupa alunos por responsável ID.
        Um aluno pode aparecer em múltiplos responsáveis.
        """
        guardian_map = defaultdict(list)

        for student in students:
            info = self._build_student_info(student)

            # Mãe
            mae_id = student.get('mae_id')
            if mae_id:
                guardian_map[mae_id].append({
                    **info,
                    '_parentesco': 'mae',
                    '_parentesco_display': 'Mãe',
                })

            # Pai
            pai_id = student.get('pai_id')
            if pai_id:
                guardian_map[pai_id].append({
                    **info,
                    '_parentesco': 'pai',
                    '_parentesco_display': 'Pai',
                })

            # Responsável principal (se não for mãe/pai)
            resp_id = student.get('responsavel_id')
            if resp_id and resp_id not in (mae_id, pai_id):
                guardian_map[resp_id].append({
                    **info,
                    '_parentesco': 'responsavel_principal',
                    '_parentesco_display': 'Responsável Principal',
                })

            # Responsável secundário (se não duplicar)
            resp2_id = student.get('responsavel_secundario_id')
            if resp2_id and resp2_id not in (mae_id, pai_id, resp_id):
                guardian_map[resp2_id].append({
                    **info,
                    '_parentesco': 'responsavel_secundario',
                    '_parentesco_display': 'Responsável Secundário',
                })

        return dict(guardian_map)

    def _build_student_info(self, student: Dict) -> Dict:
        """
        Constrói dict de um aluno com campos padronizados.
        Inclui TUDO que pode ser necessário (list ou detail).
        """
        return {
            'id': student.get('id'),
            'nome': student.get('nome'),
            'matricula': student.get('matricula'),
            'turma': student.get('_turma'),
            'serie': student.get('_serie'),
            'turma_nome': student.get('_turma_nome'),
            'periodo': extrair_periodo(student.get('_turma_nome')),
            'status': mapear_status(student.get('_situacao')),
            'url_foto': student.get('url_foto'),
        }

    # -----------------------------------------------------------------
    # CONSTRUÇÃO DO DICT DO RESPONSÁVEL
    # -----------------------------------------------------------------

    def _build_guardian_dict(
        self, guardian: Dict, children: List[Dict]
    ) -> Dict:
        """
        Constrói dict COMPLETO do responsável.
        Inclui TODOS os campos do SIGA — os serializers filtram.
        """
        # Parentesco (do primeiro filho, se houver)
        parentesco = 'responsavel'
        parentesco_display = 'Responsável'
        if children:
            parentesco = children[0].get('_parentesco', 'responsavel')
            parentesco_display = children[0].get(
                '_parentesco_display', 'Responsável'
            )

        # Limpar campos internos (_parentesco) dos filhos
        filhos_clean = []
        for child in children:
            filhos_clean.append({
                k: v for k, v in child.items()
                if not k.startswith('_')
            })

        # Documentos (baseado em campos preenchidos)
        documentos = self._build_documents(guardian)

        # Estado civil mapeado
        estado_civil_raw = guardian.get('estado_civil')
        estado_civil = ESTADO_CIVIL_MAP.get(
            str(estado_civil_raw), None
        ) if estado_civil_raw else None

        # Data nascimento limpa (só data, sem horário)
        data_nasc_raw = guardian.get('data_nascimento')
        data_nascimento = None
        if data_nasc_raw:
            data_nascimento = str(data_nasc_raw).split('T')[0]

        return {
            # --- Dados básicos (usados na LISTA e DETALHE) ---
            'id': guardian.get('id'),
            'nome': guardian.get('nome'),
            'cpf': guardian.get('cpf_cnpj') or guardian.get('cpf'),
            'email': guardian.get('email'),
            'telefone': guardian.get('celular'),
            'sexo': guardian.get('sexo'),

            # --- Dados extras (usados só no DETALHE) ---
            'telefone_fixo': guardian.get('fone'),
            'data_nascimento': data_nascimento,
            'estado_civil': estado_civil,
            'rg': guardian.get('rg'),
            'rg_orgao': guardian.get('rg_orgao_emissor'),
            'profissao': guardian.get('profissao_nome'),
            'local_trabalho': guardian.get('local_trabalho'),

            # --- Endereço ---
            'endereco': {
                'logradouro': guardian.get('logradouro'),
                'complemento': guardian.get('complemento'),
                'bairro': guardian.get('bairro'),
                'cidade': guardian.get('cidade'),
                'uf': guardian.get('uf'),
                'cep': guardian.get('cep'),
            },

            # --- Parentesco ---
            'parentesco': parentesco,
            'parentesco_display': parentesco_display,

            # --- Filhos e documentos ---
            'filhos': filhos_clean,
            'documentos': documentos,
        }

    # -----------------------------------------------------------------
    # DOCUMENTOS (gerados a partir de campos preenchidos)
    # -----------------------------------------------------------------

    def _build_documents(self, guardian: Dict) -> List[Dict]:
        """
        Gera lista de documentos baseado em campos preenchidos.
        O SIGA não tem endpoint de documentos — deduzimos do cadastro.
        """
        docs = []
        doc_id = 1

        fields_map = [
            ('cpf_cnpj', 'cpf', 'CPF'),
            ('rg', 'rg', 'RG'),
            ('email', 'email', 'Email'),
            ('celular', 'telefone', 'Telefone'),
            ('cep', 'comprovante_residencia', 'Comprovante de Residência'),
        ]

        for siga_field, tipo, nome in fields_map:
            value = guardian.get(siga_field)
            is_filled = bool(value and str(value).strip())

            docs.append({
                'id': doc_id,
                'tipo': tipo,
                'nome': nome,
                'status': 'entregue' if is_filled else 'pendente',
                'data_entrega': None,  # SIGA não fornece
            })
            doc_id += 1

        return docs