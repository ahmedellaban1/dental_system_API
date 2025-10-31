from functools import wraps
from django.shortcuts import redirect

def patient_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if getattr(request.user, "type", None) != "patient":
                return redirect('/home/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def doctor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if getattr(request.user, "type", None) != "doctor":
                return redirect('/home/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if getattr(request.user, "type", None) != "admin":
                return redirect('/home/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def receptionist_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if getattr(request.user, "type", None) != "receptionist":
                return redirect('/home/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def medical_rep_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if getattr(request.user, "type", None) != "medical_rep":
                return redirect('/home/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view