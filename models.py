from datetime import datetime


# Sistemdeki tüm kullanıcı tipleri için temel sınıf.
# Ortak olarak kullanıcı adı bilgisini tutar.
class Person:

    # Kullanıcı adı bilgisi atanır
    def __init__(self, username):
        self.username = username


# Müşteri sınıfı.
# Person sınıfından kalıtım alır ve ek olarak e-posta bilgisi tutar.
class Customer(Person):

    # Müşteri bilgileri oluşturulur
    def __init__(self, username, email):

        # Person sınıfının constructor'ı çağrılır
        super().__init__(username)

        # Müşterinin e-posta bilgisi tutulur
        self.email = email


# Teknisyen sınıfı.
# Person sınıfından kalıtım alır.
class Technician(Person):

    # Teknisyen kullanıcı adı bilgisi oluşturulur
    def __init__(self, username):

        # Person constructor'ı çağrılır
        super().__init__(username)


# Usta sınıfı.
# Person sınıfından kalıtım alır.
class Master(Person):

    # Usta kullanıcı adı bilgisi oluşturulur
    def __init__(self, username):

        # Person constructor'ı çağrılır
        super().__init__(username)


# Sisteme kayıtlı kullanıcı hesap bilgilerini tutan sınıf.
class UserAccount:

    # Kullanıcı hesabı bilgileri oluşturulur
    def __init__(self, username, password_hash, role, email=""):

        # Kullanıcı adı
        self.username = username

        # Şifrelenmiş parola
        self.password_hash = password_hash

        # Kullanıcı rolü
        self.role = role

        # E-posta bilgisi
        self.email = email


# Cihaz bilgilerini tutan sınıf.
class Device:

    # Cihaz modeli ve seri numarası bilgileri oluşturulur
    def __init__(self, brand_model, serial_number):

        # Marka / model bilgisi
        self.brand_model = brand_model

        # Seri numarası bilgisi
        self.serial_number = serial_number


# Tamir kaydı bilgilerini tutan ana sınıf.
class Repair:

    # Tamir kaydı oluşturulur
    def __init__(
        self,
        repair_id,
        customer_name,
        technician_name,
        device,
        damage_desc,
        status="Pending",
        price=0.0,
        estimated_time="-",
        payment_status="Unpaid",
        process_date=""
    ):

        # Kayıt numarası
        self.repair_id = repair_id

        # Müşteri adı
        self.customer_name = customer_name

        # Teknisyen adı
        self.technician_name = technician_name

        # Device nesnesi
        self.device = device

        # Hasar açıklaması
        self.damage_desc = damage_desc

        # Tamir durumu
        self.status = status

        # Tamir fiyatı
        self.price = price

        # Tahmini tamir süresi
        self.estimated_time = estimated_time

        # Ödeme durumu
        self.payment_status = payment_status

        # İşlem tarihi
        self.process_date = process_date

    # Nesneyi tuple formatına dönüştürür.
    # Özellikle tablo ve veritabanı işlemlerinde kullanılır.
    def to_tuple(self):

        return (
            self.repair_id,
            self.customer_name,
            self.technician_name,
            self.device.brand_model,
            self.device.serial_number,
            self.damage_desc,
            self.status,
            self.price,
            self.estimated_time,
            self.payment_status,
            self.process_date
        )


# Cihaz geçmiş kayıtlarını tutan sınıf.
class RepairHistory:

    # Seri numarasına ait geçmiş listesi oluşturulur
    def __init__(self, serial_number):

        # Cihaz seri numarası
        self.serial_number = serial_number

        # Geçmiş kayıt listesi
        self.history_list = []

    # Yeni geçmiş kaydı ekler
    def add_record(self, process_date, damage_desc, status, price, delivery_date="-"):

        # Geçmiş listesine yeni kayıt eklenir
        self.history_list.append({
            "process_date": process_date,
            "damage_desc": damage_desc,
            "status": status,
            "price": price,
            "delivery_date": delivery_date
        })


# Ödeme bilgilerini tutan sınıf.
class Payment:

    # Ödeme nesnesi oluşturulur
    def __init__(self, amount, status="Unpaid"):

        # Ödeme miktarı
        self.amount = amount

        # Ödeme durumu
        self.status = status

    # Ödeme durumunu Paid yapar
    def mark_as_paid(self):
        self.status = "Paid"


# Garanti bilgilerini tutan sınıf.
class Warranty:

    # Garanti bilgileri oluşturulur
    def __init__(self, serial_number, expiry_date):

        # Seri numarası
        self.serial_number = serial_number

        # Garanti bitiş tarihi
        self.expiry_date = expiry_date


# Yedek parça bilgilerini tutan sınıf.
class SparePart:

    # Parça bilgileri oluşturulur
    def __init__(self, name, price, stock):

        # Parça adı
        self.name = name

        # Parça fiyatı
        self.price = price

        # Stok miktarı
        self.stock = stock


# Hangi tamirde hangi parçanın kullanıldığını tutan sınıf.
class PartUsage:

    # Parça kullanım bilgileri oluşturulur
    def __init__(self, repair_id, part_name, quantity):

        # Tamir kayıt numarası
        self.repair_id = repair_id

        # Kullanılan parça adı
        self.part_name = part_name

        # Kullanılan miktar
        self.quantity = quantity


# Servis merkezi bilgilerini tutan sınıf.
class ServiceCenter:

    # Servis merkezi oluşturulur
    def __init__(self, name, location):

        # Servis merkezi adı
        self.name = name

        # Konum bilgisi
        self.location = location


# Randevu bilgilerini tutan sınıf.
class Appointment:

    # Randevu nesnesi oluşturulur
    def __init__(self, repair_id, customer, technician, date, time, delivery_date):

        # Tamir kayıt numarası
        self.repair_id = repair_id

        # Müşteri adı
        self.customer = customer

        # Teknisyen adı
        self.technician = technician

        # Randevu tarihi
        self.date = date

        # Randevu saati
        self.time = time

        # Tahmini teslim tarihi
        self.delivery_date = delivery_date


# Kullanıcı geri bildirimlerini tutan sınıf.
class Feedback:

    # Feedback bilgileri oluşturulur
    def __init__(self, customer, rating, comment):

        # Müşteri adı
        self.customer = customer

        # Puan bilgisi
        self.rating = rating

        # Yorum bilgisi
        self.comment = comment


# Fatura bilgilerini tutan sınıf.
class Invoice:

    # Fatura nesnesi oluşturulur
    def __init__(self, repair_id, amount):

        # Tamir kayıt numarası
        self.repair_id = repair_id

        # Fatura tutarı
        self.amount = amount


# Kullanıcı mesajlarını tutan sınıf.
class Message:

    # Mesaj nesnesi oluşturulur
    def __init__(self, sender, receiver, content, date=None):

        # Gönderen kullanıcı
        self.sender = sender

        # Alıcı kullanıcı
        self.receiver = receiver

        # Mesaj içeriği
        self.content = content

        # Mesaj tarihi verilmezse otomatik oluşturulur
        self.date = date or datetime.now().strftime("%d/%m/%Y %H:%M")


# Bildirim detaylarını tutan sınıf.
class NotificationDetail:

    # Bildirim nesnesi oluşturulur
    def __init__(self, title, message, recipient="", date=None, is_read=0, notification_id=None):

        # Bildirim ID bilgisi
        self.notification_id = notification_id

        # Bildirim başlığı
        self.title = title

        # Bildirim mesajı
        self.message = message

        # Bildirimin gönderileceği kullanıcı
        self.recipient = recipient

        # Tarih verilmezse otomatik tarih oluşturulur
        self.date = date or datetime.now().strftime("%d/%m/%Y %H:%M")

        # Bildirimin okunup okunmadığı bilgisi
        self.is_read = is_read