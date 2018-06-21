from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.views.decorators.gzip import gzip_page
from django.db import transaction
from django.shortcuts import redirect, render
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
import os

from . forms import RoomForm

from parameters import parameters

import game.room.dashboard
import game.params.dashboard
import dashboard.tablets.client


class LoginView(TemplateView):

    template_name = "components/login.html"

    def get_context_data(self, **kwargs):

        context = super(LoginView, self).get_context_data(**kwargs)

        return context

    @classmethod
    def login(cls, request):

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            # utils.log("Logging {} user.".format(user), f=login)
            login(request, user)
            return redirect("/room_management/")

        return render(request, cls.template_name, {"fail": True})

    @classmethod
    def logout(cls, request):

        logout(request)
        return redirect("/")


@method_decorator(login_required, name='dispatch')
class NewRoomView(TemplateView):

    template_name = "components/new_room.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context.update({"subtitle": "Set number of types"})

        return context

    def post(self, request, *args, **kwargs):

        """
        Room creation process
        :param request: using POST request
        :return: html room form template (success or fail)
        """
        n_type = request.POST.get("nType")

        if n_type:
            form = RoomForm(n_type=n_type)
        else:
            form = RoomForm(request.POST)

        if form.is_valid() and not n_type:

            with transaction.atomic():
                # Create room
                game.room.dashboard.create(form.get_data())

            return redirect("/room_management")

        context = {"subtitle": "Set parameters and create a room", "form": form}
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class RoomManagementView(TemplateView):

    template_name = "components/room_management.html"
    room_data_template = "components/room_data.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context.update({'subtitle': "Room list"})

        # Get list of existing rooms and players
        rooms_list = game.room.dashboard.get_list()

        context.update({"rooms": rooms_list})

        return context

    @staticmethod
    def post(request, *args, **kwargs):

        if "delete" in request.POST:
            room_id = request.POST["delete"]

            # Delete room
            game.room.dashboard.delete(room_id=room_id)

        return redirect("/room_management")

    def get(self, request, *args, **kwargs):

        if "room_id" in request.GET:
            room_id = request.GET["room_id"]

            context = {"subtitles": f"Room {room_id}"}
            return render(request, self.room_data_template, context)

        return super().get(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class DataView(TemplateView):
    template_name = "components/data.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context.update({"subtitle": "Download data"})
        return context

    def dispatch(self, request, *args, **kwargs):

        if "sqlite" in request.GET:
            return self.convert_data_to_sqlite()

        if "flush" in request.GET:
            game.room.dashboard.flush_db()

        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def convert_data_to_sqlite():

        url = game.room.dashboard.convert_data_to_sqlite()
        return JsonResponse({"url": url})


@method_decorator(gzip_page, name='dispatch')
@method_decorator(login_required, name='dispatch')
class LogsView(TemplateView):
    template_name = "components/logs.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context.update({"subtitle": "Logs"})

        if os.path.exists(parameters.logs_path):
            files = sorted(
                [f for f in os.listdir(parameters.logs_path)
                 if os.path.isfile("".join([parameters.logs_path, f]))]
            )
            current_file = files[-1]
        else:
            files = []
            current_file = []

        context.update({"current_file": current_file})
        context.update({"logs": self.refresh_logs(current_file)})
        context.update({"files": files})

        return context

    def dispatch(self, request, *args, **kwargs):

        if "refresh_logs" in request.GET:
            if request.GET["refresh_logs"]:

                filename = request.GET["filename"]
                n_lines = int(request.GET["n_lines"])

                return JsonResponse({
                    "logs": self.refresh_logs(filename, n_lines)
                })

        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def refresh_logs(filename, n_lines=None):

        f = parameters.logs_path + filename
        if os.path.exists(f):
            with open(parameters.logs_path + filename, "r") as f:
                logs = "".join(f.readlines()[-500:])
            return logs


@method_decorator(login_required, name='dispatch')
class SettingsView(TemplateView):
    template_name = "components/settings.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context.update({"subtitle": "Settings"})

        # Get values for parameters
        params = game.params.dashboard.get_parameters()
        context.update({"params": params})

        return context

    def post(self, request, *args, **kwargs):

        for k, v in request.POST.items():
            value = v == "on"
            game.params.dashboard.set_parameter(k, value)

        return HttpResponse("Ok")


@method_decorator(login_required, name='dispatch')
class ConnectedTablets(TemplateView):
    template_name = "components/connected_tablets.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context.update({"subtitle": "Connected tablets"})

        # Get values for parameters
        devices = dashboard.tablets.client.get_connected_users()
        context.update({"devices": devices})

        return context

    @staticmethod
    def get_table_from_devices(devices):
        return render_to_string('components/connection_table.html', {'devices': devices})


