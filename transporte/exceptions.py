class TransporteErro(Exception):
    """Exceção base de domínio para o módulo de transporte urbano acessível."""


class VeiculoNaoEncontrado(TransporteErro):
    """Veículo não existe ou não está com acessibilidade física ativa."""


class PontoParadaNaoEncontrado(TransporteErro):
    """Ponto de parada informado não existe."""

