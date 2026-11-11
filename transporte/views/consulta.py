from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View


class LinhaAcessivelConsultaView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "transporte/consulta.html")
