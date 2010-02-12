#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 W-Mark Kubacki; wmark@hurrikane.de
# for parts of this work, as stated below:
# Copyright 2005-2009 Kevin Dangoor and contributors. TurboGears is a trademark of Kevin Dangoor.
#
# This module is designed as similar to TurboGears' (TG) as possible.
# Documentation of parameters for validate is from TG.
#

import functools
from inspect import getargspec

from formencode import ForEach
from formencode import national

from formencode.validators import *
from formencode.compound import *
from formencode.api import Invalid, NoDefault
from formencode.schema import Schema

from web import HTTPError

class InputInvalidException(HTTPError):
    def __init__(self, log_message=None):
        HTTPError.__init__(self, 400, log_message)


def error_handler(call_on_errors):
    """Use this decorator to have another method run for dealing with validation errors.

    For example, you have a method '/new' which features a form and a method '/create'
    which actually processes its data (after an POST request). The latter has validators
    set and thus yields an exception if they fail. By having @error_handler set for '/new'
    that method is invoked instead of '/create' on errors, receives all the data with
    error messages and can re-display the form for the user to correct what he provided.

    @param call_on_errors:
    @type call_on_errors: callable
    """
    assert callable(call_on_errors)
    def entangle(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                return method(self, *args, **kwargs)
            except InputInvalidException:
                return call_on_errors(self, *args, **kwargs)
        return wrapper
    return entangle

def validate(form=None, validators=None, state_factory=None):
    """Use this decorator to have user input validated before the decorated function is
    called.

    If the decorated function understands parameter 'validation_errors', validation
    errors are passed by that param as dict. Else, an exception is thrown which likely
    either triggers @error_handler, or yields in HTTP error 4xx.

    These variables will always be set:
    'request.validation_errors', 'request.input_values', 'request.validation_state',
    'validation_exception'.
    These variables will eventually be set:
    'validated_form'.

    @param form: a form instance that must be passed throught the validation
    process... you must give a the same form instance as the one that will
    be used to post data on the controller you are putting the validate
    decorator on.
    @type form: a form instance

    @param validators: individual validators to use for parameters.
    If you use a schema for validation then the schema instance must
    be the sole argument.
    If you use simple validators, then you must pass a dictionary with
    each value name to validate as a key of the dictionary and the validator
    instance (eg: tg.validators.Int() for integer) as the value.
    @type validators: dictionary or schema instance

    @param state_factory: If this is None, the initial state for validation
    is set to None, otherwise this must be a callable that returns the initial
    state to be used for validation.
    @type state_factory: callable or None
    """
    assert form or validators
    if callable(form) and not hasattr(form, "validate"):
        init_form = form
    else:
        init_form = lambda self: form
    def entangle(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            request = self.request
            # do not validate a second time if already validated
            if hasattr(request, 'validation_state'):
                return method(self, *args, **kwargs)

            kw = dict([(k,v if len(v) > 1 else v[0]) for k,v in request.arguments.iteritems()])
            form = init_form(self)

            errors = {}
            if state_factory is not None:
                state = state_factory()
            else:
                state = None

            if form:
                value = kw.copy()
                try:
                    kw.update(form.validate(value, state))
                except Invalid, e:
                    errors = e.unpack_errors()
                    request.validation_exception = e
                request.validated_form = form

            if validators:
                if isinstance(validators, dict):
                    for field, validator in validators.iteritems():
                        try:
                            kw[field] = validator.to_python(
                                kw.get(field, None), state)
                        except Invalid, error:
                            errors[field] = error
                else:
                    try:
                        value = kw.copy()
                        kw.update(validators.to_python(value, state))
                    except Invalid, e:
                        errors = e.unpack_errors()
                        request.validation_exception = e
            request.validation_errors = errors
            request.input_values = kw.copy()
            request.validation_state = state

            if errors:
                if 'validation_errors' in getargspec(method).args:
                    kwargs['validation_errors'] = errors
                else:
                    raise InputInvalidException()
            return method(self, *args, **kwargs)

        return wrapper
    return entangle
