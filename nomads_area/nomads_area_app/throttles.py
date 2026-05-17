from rest_framework.throttling import AnonRateThrottle

class FormSubmitThrottle(AnonRateThrottle):
    scope = "forms"