class AgendamentoErro(Exception):
    """Exceção base de domínio para agendamentos e transporte hospitalar."""


class VagaIndisponivel(AgendamentoErro):
    """Vaga já ocupada ou conflito de horário para o mesmo paciente."""


class AgendamentoNaoEncontrado(AgendamentoErro):
    """Protocolo inexistente ou solicitante sem permissão sobre o paciente."""


class PrazoMinimo24hConsulta(AgendamentoErro):
    """Tentativa de cancelar ou remarcar consulta faltando menos de 24 horas para o atendimento."""


class PrazoMinimo48hTransporte(AgendamentoErro):
    """Tentativa de solicitar transporte hospitalar faltando menos de 48 horas para a consulta."""


class SemVagaFrotaAdaptada(AgendamentoErro):
    """Frota adaptada sem saldo de vagas de cadeirante para a data/horário."""


class ComprovanteInvalido(AgendamentoErro):
    """Assinatura HMAC do QR Code inválida ou adulterada."""

