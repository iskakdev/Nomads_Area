from rest_framework.throttling import UserRateThrottle

class FormSubmitThrottle(UserRateThrottle):
    scope = "forms"
    rate = "15/hour"
