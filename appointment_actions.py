import customtkinter as ctk

from models import Appointment
from helpers import DateHelper


# Randevu işlemlerini yöneten action sınıfı.
# Müşterinin randevu oluşturmasını ve mevcut randevuları görüntülemesini sağlar.
class AppointmentActions:

    # Seçilen tamir kaydı için yeni randevu oluşturur.
    def create_appointment(self):

        # Tablodan seçilen kaydı alır
        item = self.get_selected_item()

        if not item:
            return

        # Seçilen kaydın bilgileri
        repair_id = item[0]
        customer_name = item[1]
        technician_name = item[2]
        status = item[6]
        estimated_time = item[8]

        # Sadece müşteri rolü randevu oluşturabilir
        if self.user_role != "Customer":
            return self.show_msg(
                "Error",
                "Only the customer can create an appointment.",
                "warning"
            )

        # Randevu yalnızca tamir aşamasındayken oluşturulabilir
        if status != "Repairing":
            return self.show_msg(
                "Error",
                "An appointment can only be created while the repair is in progress.",
                "warning"
            )

        # Randevu oluşturma penceresi
        win = ctk.CTkToplevel(self)
        win.title("Create Appointment")
        win.geometry("500x470")
        win.resizable(False, False)
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        # Ana kart alanı
        card = ctk.CTkFrame(win, corner_radius=22)
        card.pack(fill="both", expand=True, padx=24, pady=24)

        # Başlık
        ctk.CTkLabel(
            card,
            text="CREATE APPOINTMENT",
            font=("Arial", 23, "bold"),
            text_color=self.primary_color
        ).pack(pady=(24, 6))

        # Kayıt numarası bilgisi
        ctk.CTkLabel(
            card,
            text=f"Record #{repair_id}",
            font=("Arial", 13),
            text_color=self.get_sub_text_color()
        ).pack(pady=(0, 18))

        # Tarih giriş alanı
        app_date_entry = ctk.CTkEntry(
            card,
            placeholder_text="Appointment Date (20/06/2026)",
            width=330,
            height=38
        )
        app_date_entry.pack(pady=8)

        # Saat giriş alanı
        app_time_entry = ctk.CTkEntry(
            card,
            placeholder_text="Appointment Time (14:30)",
            width=330,
            height=38
        )
        app_time_entry.pack(pady=8)

        # Teknisyen ve tahmini süre bilgisi kutusu
        info_box = ctk.CTkFrame(card, corner_radius=16)
        info_box.pack(fill="x", padx=35, pady=16)

        ctk.CTkLabel(
            info_box,
            text=f"Technician: {technician_name}",
            font=("Arial", 13, "bold")
        ).pack(pady=(10, 3))

        ctk.CTkLabel(
            info_box,
            text=f"Estimated Repair Time: {estimated_time}",
            font=("Arial", 13)
        ).pack(pady=(0, 10))

        # Randevuyu kaydeden iç fonksiyon
        def save_appointment():

            # Kullanıcının girdiği tarih ve saat bilgileri
            app_date = app_date_entry.get().strip()
            app_time = app_time_entry.get().strip()

            # Tarih veya saat boş bırakılamaz
            if not app_date or not app_time:
                return self.show_msg(
                    "Error",
                    "Date and time cannot be empty.",
                    "warning",
                    win
                )

            # Geçmiş tarih kontrolü
            past_result = self.is_past_date(app_date)

            # Tarih formatı hatalıysa
            if past_result is None:
                return self.show_msg(
                    "Error",
                    "Date format must be DD/MM/YYYY.",
                    "warning",
                    win
                )

            # Geçmiş tarihe randevu alınamaz
            if past_result:
                return self.show_msg(
                    "Error",
                    "Past dates cannot be selected.",
                    "warning",
                    win
                )

            # Tahmini tamir süresine göre teslim tarihi hesaplanır
            delivery_date = DateHelper.add_days_to_date(
                app_date,
                estimated_time
            )

            # Teslim tarihi hesaplanamazsa hata verir
            if delivery_date is None:
                return self.show_msg(
                    "Error",
                    "Delivery date could not be calculated.",
                    "warning",
                    win
                )

            # Appointment nesnesi oluşturulur
            appointment = Appointment(
                repair_id,
                customer_name,
                technician_name,
                app_date,
                app_time,
                delivery_date
            )

            # Veritabanına kaydedilir
            self.db.add_appointment(appointment)

            # Başarı mesajı gösterilir
            self.show_msg(
                "Success",
                f"Appointment created.\nDelivery Date: {delivery_date}",
                "info",
                win
            )

            # Pencere kapatılır
            win.destroy()

        # Butonların bulunduğu alan
        button_frame = ctk.CTkFrame(card, fg_color="transparent")
        button_frame.pack(pady=12)

        # Randevu oluşturma butonu
        ctk.CTkButton(
            button_frame,
            text="Create Appointment",
            width=170,
            height=38,
            fg_color=self.primary_color,
            command=save_appointment
        ).pack(side="left", padx=8)

        # İptal butonu
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=120,
            height=38,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=win.destroy
        ).pack(side="left", padx=8)

    # Kullanıcının randevularını görüntüler
    def show_appointments(self):

        # Veritabanından randevuları çeker
        rows = self.db.get_appointments(
            self.current_user,
            self.user_role
        )

        # Randevu görüntüleme penceresi
        win = ctk.CTkToplevel(self)
        win.title("My Appointments")
        win.geometry("650x560")
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        # Ana kart alanı
        main_card = ctk.CTkFrame(win, corner_radius=22)
        main_card.pack(fill="both", expand=True, padx=24, pady=24)

        # Başlık
        ctk.CTkLabel(
            main_card,
            text="MY APPOINTMENTS",
            font=("Arial", 24, "bold"),
            text_color=self.primary_color
        ).pack(pady=(22, 6))

        # Scrollable alan
        scroll = ctk.CTkScrollableFrame(main_card, corner_radius=16)
        scroll.pack(fill="both", expand=True, padx=20, pady=12)

        # Hiç randevu yoksa mesaj gösterir
        if not rows:

            ctk.CTkLabel(
                scroll,
                text="No appointment found.",
                font=("Arial", 14),
                text_color=self.get_sub_text_color()
            ).pack(pady=40)

        else:

            # Her randevu için kart oluşturur
            for repair_id, customer, technician, app_date, app_time, delivery_date in rows:

                card = ctk.CTkFrame(scroll, corner_radius=16)
                card.pack(fill="x", padx=10, pady=10)

                # Kayıt numarası başlığı
                ctk.CTkLabel(
                    card,
                    text=f"Record #{repair_id}",
                    font=("Arial", 16, "bold"),
                    text_color=self.primary_color
                ).pack(anchor="w", padx=18, pady=(14, 6))

                # Görüntülenecek detaylar
                details = [
                    ("Customer", customer),
                    ("Technician", technician),
                    ("Appointment Date", app_date),
                    ("Appointment Time", app_time),
                    ("Delivery Date", delivery_date)
                ]

                # Her bilgi satırını ekrana yerleştirir
                for label, value in details:

                    row = ctk.CTkFrame(card, fg_color="transparent")
                    row.pack(fill="x", padx=18, pady=3)

                    ctk.CTkLabel(
                        row,
                        text=label + ":",
                        font=("Arial", 13, "bold"),
                        width=135,
                        anchor="w"
                    ).pack(side="left")

                    ctk.CTkLabel(
                        row,
                        text=str(value),
                        font=("Arial", 13),
                        anchor="w"
                    ).pack(side="left")

        # Pencereyi kapatma butonu
        ctk.CTkButton(
            main_card,
            text="Close",
            width=170,
            height=36,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=win.destroy
        ).pack(pady=(8, 18))