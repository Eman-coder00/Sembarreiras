class ContaErro(Exception):
    """Exceção base de domínio para o app contas."""


class CpfJaCadastrado(ContaErro):
    """CPF informado já está registrado."""


class EmailJaCadastrado(ContaErro):
    """E-mail informado já está registrado."""


class CepNaoLocalizado(ContaErro):
    """CEP não encontrado na base local."""


class CredenciaisInvalidas(ContaErro):
    """Identificador, senha ou perfil selecionado inválidos."""


class ContaTemporariamenteBloqueada(ContaErro):
    """Conta bloqueada por excesso de tentativas incorretas ou bloqueio administrativo."""


class SenhaAtualInvalida(ContaErro):
    """Reautenticação falhou para alteração de dados sensíveis."""


class VinculoInvalido(ContaErro):
    """Operação de vínculo de cuidador inválida ou código OTP incorreto."""


class TokenRecuperacaoInvalido(ContaErro):
    """Código de recuperação de senha inválido, expirado ou já utilizado."""


class PermissaoNegadaTitular(ContaErro):
    """Solicitante não é o titular PCD nem cuidador com vínculo aprovado."""

