from datetime import time, timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from agendamentos.models import (
    EspecialidadeADEFAL,
    UnidadeADEFAL,
    VagaAgendaADEFAL,
    VagaFrotaAdaptada,
)
from contas.models import CepLocal
from transporte.models import (
    LinhaOnibus,
    PontoParada,
    TipoEquipamentoOnibus,
    VeiculoAdaptado,
)


class DadosIniciaisService:
    @staticmethod
    def carregar_tudo() -> dict[str, int]:
        with transaction.atomic():
            total_ceps = DadosIniciaisService._carregar_ceps_maceio()
            total_linhas, total_veiculos = (
                DadosIniciaisService._carregar_transporte_maceio()
            )
            total_vagas, total_frota = (
                DadosIniciaisService._carregar_agenda_e_frota_adefal()
            )

        return {
            "ceps": total_ceps,
            "linhas": total_linhas,
            "veiculos": total_veiculos,
            "vagas_adefal": total_vagas,
            "frota_adaptada": total_frota,
        }

    @staticmethod
    def _carregar_ceps_maceio() -> int:
        ceps = [
            (
                "57051-190",
                "Rua Clementino do Monte (Sede ADEFAL)",
                "Farol",
                "Maceió",
                "AL",
            ),
            (
                "57051-000",
                "Avenida Fernandes Lima",
                "Farol",
                "Maceió",
                "AL",
            ),
            (
                "57010-000",
                "Avenida Siqueira Campos",
                "Trapiche da Barra",
                "Maceió",
                "AL",
            ),
            (
                "57030-000",
                "Avenida Doutor Antônio Gouveia",
                "Pajuçara",
                "Maceió",
                "AL",
            ),
            (
                "57035-000",
                "Avenida Álvaro Otacílio",
                "Ponta Verde",
                "Maceió",
                "AL",
            ),
            (
                "57084-000",
                "Avenida Cachoeira do Meirim",
                "Benedito Bentes",
                "Maceió",
                "AL",
            ),
        ]
        for cep, logradouro, bairro, municipio, uf in ceps:
            CepLocal.objects.update_or_create(
                cep=cep,
                defaults={
                    "logradouro": logradouro,
                    "bairro": bairro,
                    "municipio": municipio,
                    "uf": uf,
                },
            )
        return len(ceps)

    @staticmethod
    def _carregar_transporte_maceio() -> tuple[int, int]:
        linhas_dados = [
            (
                "051",
                "Santos Dumont / Trapiche (Via Farol - Sede ADEFAL)",
                "Santos Dumont, Tabuleiro, Av. Fernandes Lima, Farol (ADEFAL), Centro, Trapiche da Barra",
            ),
            (
                "704",
                "Benedito Bentes / Ponta Verde (Via Farol)",
                "Benedito Bentes, Gruta de Lourdes, Farol (ADEFAL), Pajuçara, Ponta Verde",
            ),
            (
                "201",
                "Circular Saúde / Trapiche — Jatiúca",
                "Trapiche da Barra, HGE, Farol (ADEFAL), Mangabeiras, Jatiúca",
            ),
        ]
        linhas_map: dict[str, Any] = {}
        for codigo, nome, itinerario in linhas_dados:
            linha, _ = LinhaOnibus.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "nome": nome,
                    "itinerario": itinerario,
                    "ativa": True,
                },
            )
            linhas_map[codigo] = linha

        ponto_adefal, _ = PontoParada.objects.update_or_create(
            nome="Parada Sede ADEFAL — Farol",
            defaults={
                "logradouro": "Rua Clementino do Monte, 225",
                "bairro": "Farol",
                "latitude": -9.64985,
                "longitude": -35.70895,
            },
        )
        ponto_adefal.linhas.set(list(linhas_map.values()))

        ponto_trapiche, _ = PontoParada.objects.update_or_create(
            nome="Terminal Trapiche / HGE",
            defaults={
                "logradouro": "Av. Siqueira Campos, 2095",
                "bairro": "Trapiche da Barra",
                "latitude": -9.67120,
                "longitude": -35.75510,
            },
        )
        ponto_trapiche.linhas.set([linhas_map["051"], linhas_map["201"]])

        ponto_centenario, _ = PontoParada.objects.update_or_create(
            nome="Praça Centenário — Farol",
            defaults={
                "logradouro": "Av. Fernandes Lima, 450",
                "bairro": "Farol",
                "latitude": -9.65620,
                "longitude": -35.72480,
            },
        )
        ponto_centenario.linhas.set(list(linhas_map.values()))

        ponto_pajucara, _ = PontoParada.objects.update_or_create(
            nome="Orla de Pajuçara — Ponto Acessível",
            defaults={
                "logradouro": "Av. Doutor Antônio Gouveia, 1100",
                "bairro": "Pajuçara",
                "latitude": -9.66840,
                "longitude": -35.71450,
            },
        )
        ponto_pajucara.linhas.set([linhas_map["704"], linhas_map["201"]])

        veiculos_dados = [
            (
                "MCZ-1042",
                linhas_map["051"],
                True,
                TipoEquipamentoOnibus.ELEVADOR_HIDRAULICO,
                2,
                -9.64610,
                -35.70620,
                24.0,
            ),
            (
                "MCZ-2088",
                linhas_map["704"],
                True,
                TipoEquipamentoOnibus.RAMPA_ACESSIVEL,
                2,
                -9.64250,
                -35.70410,
                26.0,
            ),
            (
                "MCZ-3115",
                linhas_map["201"],
                True,
                TipoEquipamentoOnibus.ELEVADOR_HIDRAULICO,
                1,
                -9.65320,
                -35.71240,
                22.0,
            ),
            (
                "MCZ-9900",
                linhas_map["051"],
                False,
                TipoEquipamentoOnibus.ELEVADOR_HIDRAULICO,
                1,
                -9.64800,
                -35.70800,
                25.0,
            ),
        ]
        for (
            prefixo,
            linha_obj,
            acessivel,
            equipamento,
            vagas,
            lat,
            lon,
            vel,
        ) in veiculos_dados:
            VeiculoAdaptado.objects.update_or_create(
                prefixo=prefixo,
                defaults={
                    "linha": linha_obj,
                    "acessibilidade_ativa": acessivel,
                    "tipo_equipamento": equipamento,
                    "vagas_cadeirante": vagas,
                    "latitude_atual": lat,
                    "longitude_atual": lon,
                    "velocidade_media_kmh": vel,
                },
            )
        return len(linhas_dados), len(veiculos_dados)

    @staticmethod
    def _carregar_agenda_e_frota_adefal() -> tuple[int, int]:
        hoje = timezone.localdate()
        dias_offset = [3, 5, 7, 10]
        grade = [
            (
                EspecialidadeADEFAL.FISIOTERAPIA,
                UnidadeADEFAL.SEDE_MACEIO,
                "Dra. Camila Rocha (Fisioterapeuta Neurofuncional)",
                time(8, 30),
            ),
            (
                EspecialidadeADEFAL.ORTOPEDIA,
                UnidadeADEFAL.SEDE_MACEIO,
                "Dr. Marcos Aurélio Lima (Ortopedista)",
                time(10, 0),
            ),
            (
                EspecialidadeADEFAL.TERAPIA_OCUPACIONAL,
                UnidadeADEFAL.SEDE_MACEIO,
                "Dra. Renata Albuquerque (Terapeuta Ocupacional)",
                time(14, 0),
            ),
            (
                EspecialidadeADEFAL.NEUROLOGIA,
                UnidadeADEFAL.UNIDADE_REGIONAL,
                "Dra. Helena Costa (Neurologista)",
                time(15, 30),
            ),
            (
                EspecialidadeADEFAL.CONSULTA_GERAL,
                UnidadeADEFAL.SEDE_MACEIO,
                "Dr. Carlos Eduardo Melo (Clínico / Triagem)",
                time(16, 30),
            ),
        ]

        total_vagas = 0
        total_frota = 0
        for offset in dias_offset:
            data_alvo = hoje + timedelta(days=offset)
            for esp, unidade, prof, horario in grade:
                VagaAgendaADEFAL.objects.get_or_create(
                    unidade=unidade,
                    profissional=prof,
                    data=data_alvo,
                    horario=horario,
                    defaults={
                        "especialidade": esp,
                        "disponivel": True,
                    },
                )
                total_vagas += 1

            VagaFrotaAdaptada.objects.get_or_create(
                data=data_alvo,
                turno_horario=time(7, 30),
                veiculo_identificacao="Van Adaptada ADEFAL 01 (Elevador Hidráulico)",
                defaults={
                    "motorista": "José Carlos Alencar",
                    "vagas_cadeirante_total": 4,
                    "vagas_cadeirante_ocupadas": 0,
                },
            )
            total_frota += 1

        return total_vagas, total_frota

