class EquipamentoErro(Exception):
    """Exceção base de domínio para o módulo de equipamentos e laudos."""


class AnexoInvalido(EquipamentoErro):
    """Extensão não permitida, magic bytes inválidos ou tamanho acima do limite."""


class SolicitacaoEquipamentoNaoEncontrada(EquipamentoErro):
    """Protocolo inexistente ou usuário sem permissão de acesso."""


class OperacaoEmprestimoInvalida(EquipamentoErro):
    """Tentativa de renovação sem justificativa ou em solicitação não entregue."""

