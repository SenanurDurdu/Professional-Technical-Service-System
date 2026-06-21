import hashlib
import re
from datetime import datetime, timedelta


# Tamir kayıtlarının geçerli durum geçişlerini yöneten sınıf.
class StatusManager:

    # Sistemde kullanılacak tüm durumlar
    STAGES = ["Pending", "Diagnosing", "Waiting Approval", "Repairing", "Completed", "Rejected"]

    # Hangi durumdan hangi duruma geçilebileceğini belirler
    VALID_TRANSITIONS = {
        "Pending": ["Diagnosing"],
        "Diagnosing": ["Waiting Approval"],
        "Waiting Approval": ["Repairing", "Rejected"],
        "Repairing": ["Completed"],
        "Completed": [],
        "Rejected": []
    }

    # Durum geçişinin geçerli olup olmadığını kontrol eder
    @staticmethod
    def is_valid_transition(current_status, next_status):

        # Geçersiz durum varsa False döndürür
        if current_status not in StatusManager.VALID_TRANSITIONS:
            return False

        # Sonraki durum izin verilenler arasında mı kontrol eder
        return next_status in StatusManager.VALID_TRANSITIONS[current_status]


# Şifre güvenliği işlemlerini yöneten sınıf.
class SecurityManager:

    # Şifrenin minimum uzunluk kontrolünü yapar
    @staticmethod
    def check_password_length(password):
        return len(password) >= 6

    # Şifreyi SHA-256 algoritması ile şifreler
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    # Girilen şifre ile kayıtlı hash değerini karşılaştırır
    @staticmethod
    def verify_password(password, hashed_password):
        return SecurityManager.hash_password(password) == hashed_password


# Sistem log işlemlerini yöneten sınıf.
class LoggerSystem:

    # Log listesini başlatır
    def __init__(self):
        self.logs = []

    # Yeni log kaydı oluşturur
    def log_action(self, action):

        # Tarih ve saat bilgisi ile log metni oluşturulur
        log_text = f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {action}"

        # Log listeye eklenir
        self.logs.append(log_text)

        # Konsola yazdırılır
        print(log_text)

    # Tüm log kayıtlarını döndürür
    def get_logs(self):
        return self.logs


# Sistem istatistiklerini hesaplayan sınıf.
class StatisticsManager:

    # Tamir kayıtlarından özet bilgiler oluşturur
    @staticmethod
    def get_summary(repairs):

        # Başlangıç değerleri
        total = len(repairs)
        pending = 0
        completed = 0
        paid = 0
        rejected = 0
        total_earnings = 0

        # Tüm kayıtlar üzerinde dolaşır
        for repair in repairs:

            # Gerekli alanlar alınır
            status = repair[6]
            price = repair[7]
            payment_status = repair[9]

            # Pending kayıt sayısı
            if status == "Pending":
                pending += 1

            # Completed kayıt sayısı
            if status == "Completed":
                completed += 1

            # Rejected kayıt sayısı
            if status == "Rejected":
                rejected += 1

            # Ödenmiş kayıt sayısı ve toplam kazanç
            if payment_status == "Paid":
                paid += 1
                total_earnings += price

        # İstatistik sözlüğü döndürülür
        return {
            "total": total,
            "pending": pending,
            "completed": completed,
            "paid": paid,
            "rejected": rejected,
            "earnings": total_earnings
        }


# Basit bildirim sistemi sınıfı.
class NotificationSystem:

    # Bildirim listesini başlatır
    def __init__(self):
        self.messages = []

    # Yeni bildirim ekler
    def add_notification(self, message):
        self.messages.append(message)

    # Tüm bildirimleri döndürür
    def get_notifications(self):
        return self.messages


# Tarih işlemlerini yöneten yardımcı sınıf.
class DateHelper:

    # Bugünün tarihini döndürür
    @staticmethod
    def get_today():
        return datetime.now().strftime("%d/%m/%Y")

    # Tahmini süreye göre teslim tarihini hesaplar
    @staticmethod
    def add_days_to_date(date_text, estimated_time):

        # Tarih formatını datetime nesnesine dönüştürür
        try:
            base_date = datetime.strptime(date_text, "%d/%m/%Y")

        # Tarih formatı hatalıysa None döndürür
        except ValueError:
            return None

        # Gereksiz boşlukları temizler
        estimated_time = estimated_time.strip()

        # Metin içerisindeki gün sayısını bulur
        match = re.search(r"^-?\d+", estimated_time)

        # Sayı bulunamazsa None döndürür
        if not match:
            return None

        # Gün sayısını integer'a çevirir
        day_count = int(match.group())

        # Gün sayısı sıfır veya negatif olamaz
        if day_count <= 0:
            return None

        # Teslim tarihi hesaplanır
        delivery_date = base_date + timedelta(days=day_count)

        # Yeni tarihi string formatında döndürür
        return delivery_date.strftime("%d/%m/%Y")


# Kullanıcının tema ve renk ayarlarını tutan sınıf.
class SystemSettings:

    # Varsayılan tema ve tema rengi bilgilerini saklar
    def __init__(self, theme="Dark", theme_color="Blue"):
        self.theme = theme
        self.theme_color = theme_color