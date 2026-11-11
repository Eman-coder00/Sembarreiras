class EmergenciaErro(Exception):
    """Exceção base de domínio para o módulo de emergência."""


class LimiteContatosExcedido(EmergenciaErro):
    """Titular já possui 3 contatos de emergência ativos ou a prioridade já está ocupada."""


class MinimoContatoAtivoObrigatorio(EmergenciaErro):
    """Tentativa de excluir ou inativar o único contato de emergência ativo da conta."""


class SemContatosDeEmergencia(EmergenciaErro):
    """Tentativa de acionar o botão de pânico sem nenhum contato ativo cadastrado."""


class OcorrenciaNaoEncontrada(EmergenciaErro):
    """Ocorrência não existe ou pertence a outro titular sem vínculo autorizado."""


class JanelaCancelamentoEncerrada(EmergenciaErro):
    """Tentativa de cancelar um alerta que já foi disparado ou encerrado."""

