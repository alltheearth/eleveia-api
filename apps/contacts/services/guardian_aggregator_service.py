# apps/contacts/services/guardian_aggregator_service.py

import logging
from typing import List, Dict, Optional
from collections import defaultdict
from ..utils.siga_helpers import extrair_periodo, mapear_status, deduzir_parentesco

logger = logging.getLogger(__name__)


class GuardianAggregatorService:
    """
    Serviço responsável por agregar e enriquecer dados dos responsáveis.
    Faz JOIN entre as 3 APIs e aplica regras de negócio.
    """

    def build_guardians_response(
            self,
            guardians: List[Dict],
            students_relations: List[Dict],
            students_academic: List[Dict]
    ) -> List[Dict]:
        """
        Constrói resposta completa com responsáveis e filhos.

        Args:
            guardians: Lista de responsáveis (API 1)
            students_relations: Lista de alunos com vínculos (API 2)
            students_academic: Lista de alunos com dados acadêmicos (API 3)

        Returns:
            Lista de dicionários formatados com responsáveis e filhos
        """
        # JOIN: Mesclar dados acadêmicos nos alunos
        students_full = self._merge_student_data(students_relations, students_academic)

        # Agrupar alunos por responsável
        guardian_students_map = self._group_students_by_guardian(students_full)

        # Construir resposta final
        result = []
        for guardian in guardians:
            guardian_id = guardian['id']
            children = guardian_students_map.get(guardian_id, [])

            guardian_dict = self._build_guardian_dict(guardian, children)
            result.append(guardian_dict)

        return result

    def _merge_student_data(
            self,
            students_relations: List[Dict],
            students_academic: List[Dict]
    ) -> List[Dict]:
        """
        Faz JOIN entre dados de relacionamento e dados acadêmicos dos alunos.

        Args:
            students_relations: Alunos com mae_id, pai_id, etc
            students_academic: Alunos com turma, série, status

        Returns:
            Lista de alunos com dados completos
        """
        # Criar índice para lookup O(1)
        academic_dict = {s['id_aluno']: s for s in students_academic}

        merged = []
        for student_rel in students_relations:
            student_id = student_rel['id']
            academic_data = academic_dict.get(student_id, {})

            # Mesclar dados
            student_full = {
                **student_rel,
                'turma': academic_data.get('nome_curso'),
                'serie': academic_data.get('nome_serie'),
                'nome_turma_raw': academic_data.get('nome_turma'),
                'situacao': academic_data.get('situacao_aluno_turma'),
            }

            merged.append(student_full)

        logger.debug(f"Merged {len(merged)} students with academic data")
        return merged

    def _group_students_by_guardian(self, students: List[Dict]) -> Dict[int, List[Dict]]:
        """
        Agrupa alunos por responsável ID.
        Um aluno pode aparecer múltiplas vezes se o responsável tem múltiplos papéis.

        Args:
            students: Lista de alunos com dados completos

        Returns:
            Dict mapeando guardian_id -> lista de alunos
        """
        guardian_map = defaultdict(list)

        for student in students:
            student_info = self._build_student_info(student)

            # Mapear por todos os papéis do responsável
            if student.get('mae_id'):
                guardian_map[student['mae_id']].append({
                    **student_info,
                    '_parentesco': 'mae',
                    '_parentesco_display': 'Mãe'
                })

            if student.get('pai_id'):
                guardian_map[student['pai_id']].append({
                    **student_info,
                    '_parentesco': 'pai',
                    '_parentesco_display': 'Pai'
                })

            if student.get('responsavel_id'):
                # Evitar duplicação se já é mãe/pai
                if student.get('responsavel_id') not in [student.get('mae_id'), student.get('pai_id')]:
                    guardian_map[student['responsavel_id']].append({
                        **student_info,
                        '_parentesco': 'responsavel_principal',
                        '_parentesco_display': 'Responsável Principal'
                    })

            if student.get('responsavel_secundario_id'):
                # Evitar duplicação
                already_mapped = [
                    student.get('mae_id'),
                    student.get('pai_id'),
                    student.get('responsavel_id')
                ]
                if student.get('responsavel_secundario_id') not in already_mapped:
                    guardian_map[student['responsavel_secundario_id']].append({
                        **student_info,
                        '_parentesco': 'responsavel_secundario',
                        '_parentesco_display': 'Responsável Secundário'
                    })

        return dict(guardian_map)

    def _build_student_info(self, student: Dict) -> Dict:
        """
        Constrói objeto de informação do aluno.

        Args:
            student: Dados completos do aluno

        Returns:
            Dict formatado para resposta
        """
        return {
            'id': student.get('id'),
            'nome': student.get('nome'),
            'turma': student.get('turma'),
            'serie': student.get('serie'),
            'periodo': extrair_periodo(student.get('nome_turma_raw')),
            'status': mapear_status(student.get('situacao')),
        }

    def _build_guardian_dict(self, guardian: Dict, children: List[Dict]) -> Dict:
        """
        Constrói dicionário completo do responsável.

        Args:
            guardian: Dados do responsável
            children: Lista de filhos

        Returns:
            Dict formatado para resposta
        """
        # Endereço
        endereco = {
            'cep': guardian.get('cep'),
            'logradouro': guardian.get('logradouro'),
            'numero': None,  # Não existe na API
            'complemento': guardian.get('complemento'),
            'bairro': guardian.get('bairro'),
            'cidade': guardian.get('cidade'),
            'estado': guardian.get('uf'),
        }

        # Documentos (gerados baseados em campos preenchidos)
        documentos = self._build_documents(guardian)

        # Determinar parentesco (do primeiro filho, se houver)
        parentesco = 'responsavel'
        parentesco_display = 'Responsável'
        if children:
            parentesco = children[0].get('_parentesco', 'responsavel')
            parentesco_display = children[0].get('_parentesco_display', 'Responsável')

        # Remover campos internos dos filhos
        filhos_clean = []
        for child in children:
            child_clean = {k: v for k, v in child.items() if not k.startswith('_')}
            filhos_clean.append(child_clean)

        return {
            'id': guardian.get('id'),
            'nome': guardian.get('nome'),
            'cpf': guardian.get('cpf') or guardian.get('cpf_cnpj'),
            'email': guardian.get('email'),
            'telefone': guardian.get('celular'),
            'endereco': endereco,
            'parentesco': parentesco,
            'parentesco_display': parentesco_display,
            'responsavel_financeiro': False,  # Hardcoded conforme solicitado
            'responsavel_pedagogico': False,  # Hardcoded conforme solicitado
            'filhos': filhos_clean,
            'documentos': documentos,
        }

    def _build_documents(self, guardian: Dict) -> List[Dict]:
        """
        Gera lista de documentos baseado em campos preenchidos.

        Args:
            guardian: Dados do responsável

        Returns:
            Lista de dicionários de documentos
        """
        documentos = []
        doc_id = 1

        # CPF
        cpf = guardian.get('cpf') or guardian.get('cpf_cnpj')
        if cpf:
            documentos.append({
                'id': doc_id,
                'tipo': 'CPF',
                'nome': 'CPF do Responsável',
                'status': None,
                'data_entrega': None,
            })
            doc_id += 1

        # Email
        if guardian.get('email'):
            documentos.append({
                'id': doc_id,
                'tipo': 'Email',
                'nome': 'Email do Responsável',
                'status': None,
                'data_entrega': None,
            })
            doc_id += 1

        # Telefone
        if guardian.get('celular'):
            documentos.append({
                'id': doc_id,
                'tipo': 'Telefone',
                'nome': 'Telefone do Responsável',
                'status': None,
                'data_entrega': None,
            })
            doc_id += 1

        return documentos