import copy
import traceback
from inspect import isclass
from typing import Any, Callable, Iterable, Mapping

from django.http.request import HttpRequest
from django.http.response import (Http404, HttpResponseBase,
                                  HttpResponseServerError)
from django.shortcuts import render
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

Serializer = type[serializers.Serializer] | serializers.Serializer
Field = type[serializers.Field] | serializers.Field
JsonValue = Mapping | Iterable | float | int | bool


class HttpResponse422(Response):
    status_code = 422

    def __init__(self, data: Any = None, *args, **kwds):
        if data is None:
            data = {}
        data = {'details': data}
        super().__init__(data=data, *args, **kwds)


class JsonChoiceField():
    ...


def restapi(
    permissions: Iterable[type[BasePermission]] | None = None,
    ajax: bool | None = None,
    query: Serializer | None = None,
    body: Serializer | None = None,
    response: openapi.Response | Serializer | Field | None = None,
    description: str | None = None,
    deprecated: bool = False,
):
    def set_func(func: Callable[..., HttpResponseBase | JsonValue | None]):
        wrapper = response_wrapper(func)
        if query or body:
            wrapper = serializer_wrapper(wrapper, func, query, body)
        if permissions:
            wrapper = permission_wrapper(wrapper, permissions)
        if ajax:
            wrapper = ajax_wrapper(wrapper)
        wrapper = schema(
            summary=func.__doc__, description=description, query=query,
            body=body, response=response, deprecated=deprecated)(wrapper)
        return wrapper
    return set_func


def response_wrapper(func: Callable[..., HttpResponseBase | JsonValue | None]):
    def wrapper(self, request: HttpRequest, *args, **kwds):
        try:
            response = func(self, request, *args, **kwds)
        except Http404 as exc:
            return HttpResponse422(str(exc))
        except Exception as exc:
            traceback.print_exception(exc)
            return HttpResponseServerError()
        if isinstance(response, HttpResponseBase):
            return response
        return Response(response)
    wrapper.__name__ = func.__name__
    return wrapper


def serializer_wrapper(
    func: Callable[..., HttpResponseBase],
    o_func: Callable[..., Any],
    query: Serializer | None = None,
    body: Serializer | None = None,
):
    need_serializer = 'serializer' in o_func.__annotations__
    need_data = 'data' in o_func.__annotations__

    def wrapper(self, request, *args, **kwds):
        if query:
            if isinstance(query, serializers.BaseSerializer):
                serializer = copy.deepcopy(query)
                serializer.initial_data = request.GET
            else:
                serializer = query(data=request.GET)
        elif body:
            if isinstance(body, serializers.BaseSerializer):
                serializer = copy.deepcopy(body)
                serializer.initial_data = request.data
            else:
                serializer = body(data=request.data)
        else:
            return HttpResponse422()
        if not serializer.is_valid():
            return HttpResponse422(serializer.errors)

        if need_serializer:
            kwds['serializer'] = serializer
        if need_data:
            kwds['data'] = serializer.data
        return func(self, request, *args, **kwds)
    wrapper.__name__ = func.__name__
    return wrapper


def permission_wrapper(
    func: Callable[..., HttpResponseBase],
    permissions: Iterable[type[BasePermission]],
):
    __permissions = [permission() for permission in permissions]

    def wrapper(self, request: HttpRequest, *args, **kwds):
        for permission in __permissions:
            if permission.has_permission(request, self):
                return func(self, request=request, *args, **kwds)
        return HttpResponse422()
    wrapper.__name__ = func.__name__
    return wrapper


def ajax_wrapper(func: Callable[..., HttpResponseBase]):
    """判断是不是ajax请求, 要求前端在标头中带上 X-Requested-With"""

    def wrapper(self, request: HttpRequest, *args, **kwds):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return func(self, request, *args, **kwds)
        return render(request, 'index.html')
    wrapper.__name__ = func.__name__
    return wrapper


class Response422Serializer(serializers.Serializer):
    details = serializers.Field()


def schema(
    query: Serializer | None = None,
    body: Serializer | None = None,
    response: openapi.Response | Serializer | Field | None = None,
    summary: str | None = None,
    description: str | None = None,
    deprecated: bool | None = None,
):
    if response is None:
        response = openapi.Response('No Response')
    elif isclass(response):
        response = response()

    return swagger_auto_schema(
        query_serializer=query,
        request_body=body,
        responses={
            200: response,
            400: {},
            422: Response422Serializer(),
        },
        operation_summary=summary,
        operation_description=description,
        deprecated=deprecated,
    )


def deprecated_api(name):
    @restapi(deprecated=True)
    def wrapper(*args, **kwds):
        return HttpResponse422()
    wrapper.__name__ = name
    return wrapper
