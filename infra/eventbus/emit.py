def emit_event(event_type: str, user=None, payload: dict = None):
    """Centralized event emitter.

    All apps should use this instead of creating Event directly.
    """
    from .models import Event

    Event.objects.create(
        user=user,
        event_type=event_type,
        payload=payload or {},
    )
