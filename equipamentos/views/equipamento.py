from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View


class EquipamentoListView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "equipamentos/lista.html")
