"""Messages des moteurs, traduisibles.

Les moteurs (sans Qt) écrivent leurs erreurs et avertissements en français :
c'est le texte des journaux, des tests et de ``str(exc)``. L'interface les
montre dans sa langue :

- un message fixe est la valeur française d'une clé du catalogue ;
  ``tr(texte)`` le traduit par l'alias français ;
- un message avec des valeurs (un sigle, un fichier…) est un ``Localized`` :
  une chaîne française qui garde sa clé et ses valeurs, pour que
  ``localized_text`` le traduise avec les mêmes valeurs.

``localized(ValueError, 'clé', sigle=…)`` construit l'exception ;
``localized_text(exc_ou_texte)`` donne le texte à afficher, et note
l'exception dans le journal des erreurs (``error_log``).
"""
from __future__ import annotations

from . import error_log
from .i18n import french, tr


class Localized(str):
    """Texte français d'une clé du catalogue, qui garde la clé et les valeurs."""

    def __new__(cls, key: str, **values):
        text = super().__new__(cls, french(key, **values))
        text.key = key
        text.values = values
        return text

    def __reduce__(self):
        return (_rebuild, (self.key, self.values))


def _rebuild(key, values):
    return Localized(key, **values)


def localized(error_type, key: str, **values):
    """Une exception *error_type* dont le message est la clé *key*."""
    return error_type(Localized(key, **values))


def localized_text(message) -> str:
    """Le texte à montrer pour *message* (exception ou texte) dans la langue
    de l'interface ; un texte inconnu du catalogue est rendu tel quel.

    Une exception montrée ainsi est aussi notée dans le journal des erreurs,
    avec sa pile d'appels si elle a été levée (une seule fois, même si son
    message en cite une autre)."""
    text = _text(message)
    if isinstance(message, BaseException):
        error_log.logger('interface').warning(
            'Erreur montrée (%s) : %s', type(message).__name__, text,
            exc_info=message if message.__traceback__ is not None else None)
    return text


def _text(message) -> str:
    if isinstance(message, BaseException):
        args = getattr(message, 'args', ())
        message = args[0] if len(args) == 1 and isinstance(args[0], str) else str(message)
    key = getattr(message, 'key', None)
    if key is not None:
        return tr(key, **{name: _text(value) if isinstance(value, (Localized, BaseException)) else value
                          for name, value in message.values.items()})
    return tr(str(message))
