from repair_actions import RepairActions
from payment_actions import PaymentActions
from appointment_actions import AppointmentActions
from communication_actions import CommunicationActions
from service_actions import ServiceActions
from helper_actions import HelperActions


# Tüm action sınıflarını tek bir yapı altında birleştiren mixin sınıfı.
# Bu yapı sayesinde TechApp sınıfı bütün action metotlarına erişebilir.
class AppActionsMixin(
    RepairActions,
    PaymentActions,
    AppointmentActions,
    CommunicationActions,
    ServiceActions,
    HelperActions
):
    pass