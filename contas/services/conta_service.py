import re
from typing import Any

from django.db import models, transaction

from contas.exceptions import (
    CepNaoLocalizado,
    CpfJaCadastrado,
    EmailJaCadastrado,
    PermissaoNegadaTitular,
    SenhaAtualInvalida,
)
from contas.models import (
    CepLocal,
    LogAuditoriaConta,
    PapelUsuario,
    PerfilPCD,
    StatusCadastro,
    StatusVinculo,
    Usuario,
    VinculoCuidador,
)


def formatar_cpf(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) != 11:
        return (valor or "").strip()
    return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"


def cpf_eh_valido(valor: str) -> bool:
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    return True


def formatar_cep(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) != 8:
        return (valor or "").strip()
    return f"{digitos[:5]}-{digitos[5:]}"


class ContaService:
    @staticmethod
    def obter_perfil_pcd(usuario: Any) -> PerfilPCD | Any:
        if not getattr(usuario, "is_authenticated", False):
            return None
        return PerfilPCD.objects.select_related("usuario").filter(usuario=usuario).first()

    @staticmethod
    def listar_logs_recentes(
        usuario: Any, limite: int = 10
    ) -> models.QuerySet[Any]:
        return LogAuditoriaConta.objects.filter(usuario=usuario)[:limite]

    @staticmethod
    def consultar_cep(cep: str) -> dict[str, str]:
        cep_formatado = formatar_cep(cep)
        registro = CepLocal.objects.filter(cep=cep_formatado).first()
        if not registro:
            raise CepNaoLocalizado("Endereço não localizado")
        return {
            "cep": registro.cep,
            "logradouro": registro.logradouro,
            "bairro": registro.bairro,
            "municipio": registro.municipio,
            "uf": registro.uf,
        }

    @staticmethod
    def cadastrar_pcd(
        *,
        cpf: str,
        nome_completo: str,
        data_nascimento: Any,
        telefone: str,
        email: str,
        senha: str,
        tipo_deficiencia: str,
        equipamentos_apoio: list[str] | str,
        cep: str,
        logradouro: str,
        numero: str,
        complemento: str = "",
        bairro: str,
        municipio: str,
        uf: str,
        ip: str = "",
    ) -> Usuario | Any:
        cpf_norm = formatar_cpf(cpf)
        email_norm = email.strip().lower()

        if Usuario.objects.filter(cpf=cpf_norm).exists():
            raise CpfJaCadastrado("CPF já cadastrado")
        if Usuario.objects.filter(email__iexact=email_norm).exists():
            raise EmailJaCadastrado("E-mail já cadastrado")

        equipamentos_str = (
            ",".join(equipamentos_apoio)
            if isinstance(equipamentos_apoio, (list, tuple))
            else str(equipamentos_apoio)
        )

        with transaction.atomic():
            usuario = Usuario(
                username=cpf_norm,
                cpf=cpf_norm,
                nome_completo=nome_completo.strip(),
                data_nascimento=data_nascimento,
                telefone=telefone.strip(),
                email=email_norm,
                papel=PapelUsuario.PCD,
                status_cadastro=StatusCadastro.ATIVO,
                is_active=True,
            )
            usuario.set_password(senha)
            usuario.save()

            PerfilPCD.objects.create(
                usuario=usuario,
                tipo_deficiencia=tipo_deficiencia,
                equipamentos_apoio=equipamentos_str or "NENHUM",
                cep=formatar_cep(cep),
                logradouro=logradouro.strip(),
                numero=numero.strip(),
                complemento=complemento.strip(),
                bairro=bairro.strip(),
                municipio=municipio.strip(),
                uf=uf.strip().upper(),
            )

            LogAuditoriaConta.objects.create(
                usuario=usuario,
                evento="CADASTRO_PCD",
                detalhes="Cadastro inicial de titular PCD realizado.",
                ip=ip[:45],
            )

        return usuario

    @staticmethod
    def atualizar_dados_pcd(
        usuario: Any,
        *,
        nome_completo: str,
        telefone: str,
        equipamentos_apoio: list[str] | str,
        cep: str,
        logradouro: str,
        numero: str,
        complemento: str = "",
        bairro: str,
        municipio: str,
        uf: str,
        senha_atual: str = "",
        ip: str = "",
    ) -> Usuario | Any:
        perfil = PerfilPCD.objects.get(usuario=usuario)
        cep_norm = formatar_cep(cep)
        telefone_norm = telefone.strip()
        logradouro_norm = logradouro.strip()
        numero_norm = numero.strip()
        bairro_norm = bairro.strip()
        municipio_norm = municipio.strip()
        uf_norm = uf.strip().upper()

        alterou_dados_criticos = (
            telefone_norm != usuario.telefone
            or cep_norm != perfil.cep
            or logradouro_norm != perfil.logradouro
            or numero_norm != perfil.numero
            or bairro_norm != perfil.bairro
            or municipio_norm != perfil.municipio
            or uf_norm != perfil.uf
        )

        if alterou_dados_criticos:
            if not senha_atual or not usuario.check_password(senha_atual):
                raise SenhaAtualInvalida(
                    "Confirme sua senha atual para alterar telefone ou endereço."
                )

        equipamentos_str = (
            ",".join(equipamentos_apoio)
            if isinstance(equipamentos_apoio, (list, tuple))
            else str(equipamentos_apoio)
        )

        with transaction.atomic():
            # O CPF nunca é alterado após o cadastro (RF-02 / RS007)
            usuario.nome_completo = nome_completo.strip()
            usuario.telefone = telefone_norm
            usuario.save(update_fields=["nome_completo", "telefone"])

            perfil.equipamentos_apoio = equipamentos_str or "NENHUM"
            perfil.cep = cep_norm
            perfil.logradouro = logradouro_norm
            perfil.numero = numero_norm
            perfil.complemento = complemento.strip()
            perfil.bairro = bairro_norm
            perfil.municipio = municipio_norm
            perfil.uf = uf_norm
            perfil.save()

            if alterou_dados_criticos:
                LogAuditoriaConta.objects.create(
                    usuario=usuario,
                    evento="ALTERACAO_DADOS_CRITICOS",
                    detalhes="Alteração autenticada de telefone e/ou endereço de embarque.",
                    ip=ip[:45],
                )

        return usuario

    @staticmethod
    def atualizar_acessibilidade(
        usuario: Any,
        *,
        tipo_deficiencia: str,
        equipamentos_apoio: list[str] | str,
        tamanho_toque: str,
        timeout_tela: str,
        alto_contraste: bool,
        ip: str = "",
    ) -> PerfilPCD | Any:
        perfil = PerfilPCD.objects.get(usuario=usuario)
        equipamentos_str = (
            ",".join(equipamentos_apoio)
            if isinstance(equipamentos_apoio, (list, tuple))
            else str(equipamentos_apoio)
        )
        with transaction.atomic():
            perfil.tipo_deficiencia = tipo_deficiencia
            if equipamentos_str:
                perfil.equipamentos_apoio = equipamentos_str
            perfil.tamanho_toque = tamanho_toque
            perfil.timeout_tela = timeout_tela
            perfil.alto_contraste = bool(alto_contraste)
            perfil.save()

            LogAuditoriaConta.objects.create(
                usuario=usuario,
                evento="ATUALIZACAO_ACESSIBILIDADE",
                detalhes=f"Toque={tamanho_toque}, AltoContraste={bool(alto_contraste)}, Timeout={timeout_tela}",
                ip=ip[:45],
            )
        return perfil

    @staticmethod
    def inativar_conta_lgpd(
        usuario: Any,
        *,
        senha_atual: str,
        ip: str = "",
    ) -> Usuario | Any:
        if not senha_atual or not usuario.check_password(senha_atual):
            raise SenhaAtualInvalida(
                "Senha atual inválida para confirmar a inativação da conta."
            )

        with transaction.atomic():
            usuario.status_cadastro = StatusCadastro.INATIVO
            usuario.is_active = False
            usuario.nome_completo = f"Titular Anonimizado #{usuario.pk}"
            usuario.email = f"inativo.{usuario.pk}@anonimizado.adefal.local"
            usuario.telefone = "(00) 00000-0000"
            usuario.versao_sessao += 1
            usuario.save()

            PerfilPCD.objects.filter(usuario=usuario).update(
                logradouro="ANONIMIZADO LGPD",
                numero="S/N",
                complemento="",
                bairro="ANONIMIZADO",
            )

            VinculoCuidador.objects.filter(titular_pcd=usuario).update(
                status=StatusVinculo.REVOGADO
            )
            VinculoCuidador.objects.filter(cuidador=usuario).update(
                status=StatusVinculo.REVOGADO
            )

            LogAuditoriaConta.objects.create(
                usuario=usuario,
                evento="INATIVACAO_LGPD",
                detalhes="Inativação lógica e mascaramento de dados pessoais conforme LGPD (RS010).",
                ip=ip[:45],
            )
        return usuario

    @staticmethod
    def obter_titular_autorizado(
        solicitante: Any,
        titular_cpf: str | None = None,
    ) -> Usuario | Any:
        if (
            not getattr(solicitante, "is_authenticated", False)
            or not solicitante.is_active
            or getattr(solicitante, "status_cadastro", None) != StatusCadastro.ATIVO
        ):
            raise PermissaoNegadaTitular("Usuário sem permissão ativa.")

        if solicitante.papel == PapelUsuario.PCD:
            if titular_cpf and formatar_cpf(titular_cpf) != solicitante.cpf:
                raise PermissaoNegadaTitular(
                    "O titular PCD só pode acessar seus próprios dados."
                )
            return solicitante

        filtros: dict[str, Any] = {
            "cuidador": solicitante,
            "status": StatusVinculo.APROVADO,
            "titular_pcd__status_cadastro": StatusCadastro.ATIVO,
            "titular_pcd__is_active": True,
        }
        if titular_cpf:
            filtros["titular_pcd__cpf"] = formatar_cpf(titular_cpf)

        vinculo = (
            VinculoCuidador.objects.select_related("titular_pcd", "titular_pcd__perfil_pcd")
            .filter(**filtros)
            .first()
        )
        if not vinculo:
            raise PermissaoNegadaTitular(
                "Cuidador não possui vínculo ativo aprovado com o titular PCD."
            )
        return vinculo.titular_pcd

    @staticmethod
    def obter_resumo_home(usuario: Any) -> dict[str, Any]:
        eh_cuidador = getattr(usuario, "papel", "") == PapelUsuario.CUIDADOR
        if eh_cuidador:
            tem_vinculo_pendente = VinculoCuidador.objects.filter(
                cuidador=usuario,
                status=StatusVinculo.PENDENTE,
            ).exists()
        else:
            tem_vinculo_pendente = VinculoCuidador.objects.filter(
                titular_pcd=usuario,
                status=StatusVinculo.PENDENTE,
            ).exists()

        titular = None
        try:
            titular = ContaService.obter_titular_autorizado(usuario)
        except PermissaoNegadaTitular:
            titular = None

        sem_contato_emergencia = False
        tem_consulta_confirmada = False
        tem_alerta_prazo = False

        if titular is not None:
            sem_contato_emergencia = not titular.contatos_emergencia.filter(
                status=1
            ).exists()
            tem_consulta_confirmada = titular.consultas.filter(
                status=1
            ).exists()
            tem_alerta_prazo = titular.solicitacoes_equipamento.filter(
                status__in=[1, 2, 3, 4]
            ).exists()

        sugestao_texto = ""
        if eh_cuidador and titular is None:
            sugestao_texto = "Ação sugerida: Confirme o código OTP com o titular PCD para liberar os serviços."
        elif not eh_cuidador and sem_contato_emergencia:
            sugestao_texto = "Ação sugerida: Cadastre ao menos 1 contato prioritário para o Botão de Pânico."
        elif tem_vinculo_pendente:
            sugestao_texto = "Ação sugerida: Há uma solicitação de vínculo de cuidador aguardando confirmação."

        return {
            "eh_cuidador": eh_cuidador,
            "titular_vinculado": titular,
            "tem_vinculo_pendente": tem_vinculo_pendente,
            "sem_contato_emergencia": sem_contato_emergencia,
            "tem_consulta_confirmada": tem_consulta_confirmada,
            "tem_alerta_prazo": tem_alerta_prazo,
            "sugestao_texto": sugestao_texto,
        }
