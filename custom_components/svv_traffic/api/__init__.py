"""API-klienter for SVV Trafikk."""

from __future__ import annotations


class SvvApiError(Exception):
    """Generell feil ved henting av data fra SVV."""


class SvvAuthError(SvvApiError):
    """Autentiseringsfeil mot DATEX (feil brukernavn/passord eller IP)."""
