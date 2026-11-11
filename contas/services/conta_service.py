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
    for indice in (9, 10):
        soma = sum(
            int(digitos[pos]) * ((indice + 1) - pos) for pos in range(indice)
        )
        resto = (soma * 10) % 11
        digito_esperado = 0 if resto == 10 else resto
        if int(digitos[indice]) != digito_esperado:
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
    def _normalizar_telefone(valor: str) -> str:
        return re.sub(r"\D", "", valor or "")

    @staticmethod
    def _cuidador_esta_nos_contatos_emergencia(
        cuidador: Any,
        titular: Any,
    ) -> bool:
        from emergencia.models import ContatoEmergencia

        tel_cuidador = ContaService._normalizar_telefone(
            getattr(cuidador, "telefone", "")
        )
        if not tel_cuidador:
            return False

        contatos = ContatoEmergencia.objects.filter(
            titular_pcd=titular,
            status=1,
        ).values_list("telefone", flat=True)
        return any(
            ContaService._normalizar_telefone(tel) == tel_cuidador
            for tel in contatos
        )

    @staticmethod
    def listar_notificacoes(usuario: Any) -> list[dict[str, Any]]:
        from django.urls import reverse
        from django.utils import timezone

        from agendamentos.models import Consulta
        from emergencia.models import ContatoEmergencia, OcorrenciaPanico
        from equipamentos.models import (
            SolicitacaoEquipamento,
            StatusSolicitacaoEquipamento,
        )
        from equipamentos.services import EquipamentoService

        eh_cuidador = getattr(usuario, "papel", "") == PapelUsuario.CUIDADOR
        titular: Any = None
        try:
            titular = ContaService.obter_titular_autorizado(usuario)
        except PermissaoNegadaTitular:
            titular = None

        notificacoes: list[dict[str, Any]] = []

        # 1. Alertas de Botão de Pânico para Cuidador cadastrado nos contatos de emergência
        if (
            eh_cuidador
            and titular is not None
            and ContaService._cuidador_esta_nos_contatos_emergencia(
                usuario, titular
            )
        ):
            ocorrencias_disparadas = (
                OcorrenciaPanico.objects.filter(
                    titular_pcd=titular,
                    status__in=["ENTREGUE", "FALLBACK_SMS", "FALHA_PARCIAL"],
                )
                .order_by("-criado_em", "-id")[:5]
            )
            for oc in ocorrencias_disparadas:
                notificacoes.append(
                    {
                        "tipo": "EMERGENCIA",
                        "nivel": "CRITICO",
                        "icone": "🚨",
                        "titulo": f"Botão de Pânico acionado por {titular.nome_completo}",
                        "descricao": (
                            f"Ocorrência {oc.codigo} disparada em "
                            f"{timezone.localtime(oc.criado_em).strftime('%d/%m/%Y às %H:%M')}. "
                            f"Localização: {oc.endereco_aproximado or 'Coordenadas registradas no histórico'}."
                        ),
                        "detalhe_extra": oc.mensagem_enviada,
                        "url": reverse("emergencia:historico"),
                        "texto_botao": "Abrir Histórico e Localização",
                    }
                )

        # 2. Aviso de segurança caso titular PCD ainda não possua contatos de emergência
        if not eh_cuidador:
            tem_contato = ContatoEmergencia.objects.filter(
                titular_pcd=usuario,
                status=1,
            ).exists()
            if not tem_contato:
                notificacoes.append(
                    {
                        "tipo": "SEGURANCA",
                        "nivel": "ALERTA",
                        "icone": "🛡️",
                        "titulo": "Botão de Pânico sem contatos configurados",
                        "descricao": (
                            "Cadastre ao menos 1 contato de emergência prioritário para habilitar o acionamento rápido do SOS."
                        ),
                        "detalhe_extra": "",
                        "url": reverse("emergencia:contatos"),
                        "texto_botao": "Cadastrar Contatos de Emergência",
                    }
                )

        # 3. Solicitações de vínculo de cuidador pendentes (OTP)
        filtro_vinculo = (
            {"cuidador": usuario, "status": StatusVinculo.PENDENTE}
            if eh_cuidador
            else {"titular_pcd": usuario, "status": StatusVinculo.PENDENTE}
        )
        vinculos_pendentes = VinculoCuidador.objects.select_related(
            "cuidador", "titular_pcd"
        ).filter(**filtro_vinculo)
        for v in vinculos_pendentes:
            if eh_cuidador:
                desc = (
                    f"Aguardando confirmação do código OTP fornecido por {v.titular_pcd.nome_completo}."
                )
            else:
                desc = (
                    f"{v.cuidador.nome_completo} ({v.cuidador.cpf}) solicitou vínculo. "
                    f"Código OTP gerado: {v.codigo_otp}."
                )
            notificacoes.append(
                {
                    "tipo": "VINCULO",
                    "nivel": "ALERTA",
                    "icone": "🔗",
                    "titulo": "Vínculo de cuidador aguardando confirmação OTP",
                    "descricao": desc,
                    "detalhe_extra": "",
                    "url": reverse("contas:vinculos"),
                    "texto_botao": "Gerenciar Vínculos",
                }
            )

        # 4. Alertas de prazo de devolução e retiradas aprovadas de equipamentos
        if titular is not None:
            for alerta in EquipamentoService.listar_alertas_vencimento(titular):
                sol = alerta["solicitacao"]
                notificacoes.append(
                    {
                        "tipo": "EQUIPAMENTO",
                        "nivel": (
                            "CRITICO"
                            if alerta["nivel"] == "URGENTE_2_DIAS"
                            else "ALERTA"
                        ),
                        "icone": "⏳",
                        "titulo": f"Prazo de empréstimo próximo do vencimento ({sol.protocolo})",
                        "descricao": alerta["mensagem"],
                        "detalhe_extra": "",
                        "url": reverse(
                            "equipamentos:detalhe",
                            kwargs={"protocolo": sol.protocolo},
                        ),
                        "texto_botao": "Renovar ou Agendar Devolução",
                    }
                )

            prontos_retirada = SolicitacaoEquipamento.objects.filter(
                beneficiario_pcd=titular,
                status=StatusSolicitacaoEquipamento.APROVADO_RETIRADA,
            )
            for sol in prontos_retirada:
                notificacoes.append(
                    {
                        "tipo": "EQUIPAMENTO",
                        "nivel": "INFO",
                        "icone": "♿",
                        "titulo": f"Equipamento aprovado para retirada ({sol.protocolo})",
                        "descricao": (
                            "Sua solicitação foi aprovada pela triagem técnica da ADEFAL e está pronta para retirada."
                        ),
                        "detalhe_extra": sol.parecer_tecnico,
                        "url": reverse(
                            "equipamentos:detalhe",
                            kwargs={"protocolo": sol.protocolo},
                        ),
                        "texto_botao": "Ver Detalhes do Pedido",
                    }
                )

            # 5. Próximas consultas confirmadas na ADEFAL
            hoje = timezone.localdate()
            consultas_futuras = (
                Consulta.objects.select_related("vaga")
                .filter(
                    paciente_pcd=titular,
                    status=1,
                    vaga__data__gte=hoje,
                )
                .order_by("vaga__data", "vaga__horario")[:5]
            )
            for c in consultas_futuras:
                notificacoes.append(
                    {
                        "tipo": "CONSULTA",
                        "nivel": "INFO",
                        "icone": "🏥",
                        "titulo": f"Consulta confirmada ({c.protocolo})",
                        "descricao": (
                            f"Atendimento em {c.vaga.data.strftime('%d/%m/%Y')} às "
                            f"{c.vaga.horario.strftime('%H:%M')} com {c.vaga.profissional}."
                        ),
                        "detalhe_extra": "",
                        "url": reverse(
                            "agendamentos:detalhe",
                            kwargs={"protocolo": c.protocolo},
                        ),
                        "texto_botao": "Ver Consulta e Comprovante",
                    }
                )

        return notificacoes

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

        titular: Any = None
        try:
            titular = ContaService.obter_titular_autorizado(usuario)
        except PermissaoNegadaTitular:
            titular = None

        sem_contato_emergencia = False
        tem_consulta_confirmada = False
        tem_alerta_prazo = False
        alerta_panico_cuidador: dict[str, Any] | None = None

        if titular is not None:
            from agendamentos.models import Consulta
            from emergencia.models import ContatoEmergencia
            from equipamentos.models import SolicitacaoEquipamento

            sem_contato_emergencia = not ContatoEmergencia.objects.filter(
                titular_pcd=titular,
                status=1,
            ).exists()
            tem_consulta_confirmada = Consulta.objects.filter(
                paciente_pcd=titular,
                status=1,
            ).exists()
            tem_alerta_prazo = SolicitacaoEquipamento.objects.filter(
                beneficiario_pcd=titular,
                status__in=[1, 2, 3, 4],
            ).exists()

        notificacoes = ContaService.listar_notificacoes(usuario)
        for item in notificacoes:
            if item["tipo"] == "EMERGENCIA":
                alerta_panico_cuidador = item
                break

        sugestao_texto = ""
        if alerta_panico_cuidador is not None:
            sugestao_texto = alerta_panico_cuidador["titulo"]
        elif eh_cuidador and titular is None:
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
            "alerta_panico_cuidador": alerta_panico_cuidador,
            "total_notificacoes": len(notificacoes),
            "sugestao_texto": sugestao_texto,
        }
