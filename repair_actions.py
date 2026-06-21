import re
import customtkinter as ctk
from tkinter import simpledialog

from models import Device, Repair
from helpers import DateHelper, StatusManager


# Arıza kaydı, durum değiştirme, teklif oluşturma ve kayıt silme işlemlerini yöneten sınıf.
class RepairActions:

    # Yeni arıza kaydı oluşturur.
    def add_rep(self):

        # Form alanlarından teknisyen, seri numarası, cihaz modeli ve hasar bilgisi alınır
        technician = self.e_tech.get().strip()
        serial_no = self.e_serial.get().strip()
        device_model = self.e_dev.get().strip()
        damage = self.e_dmg.get().strip()

        # Zorunlu alanlar boş bırakılamaz
        if not serial_no or not device_model or not damage:
            return self.show_msg("Error", "Please fill in all device information.", "warning")

        # Device nesnesi oluşturulur
        device = Device(device_model, serial_no)

        # Yeni Repair nesnesi varsayılan Pending durumu ile oluşturulur
        repair = Repair(
            repair_id=None,
            customer_name=self.current_user,
            technician_name=technician,
            device=device,
            damage_desc=damage,
            status="Pending",
            price=0,
            estimated_time="-",
            payment_status="Unpaid",
            process_date=DateHelper.get_today()
        )

        # Arıza kaydı veritabanına eklenir
        success, msg = self.db.add_repair(repair)

        # Kayıt eklenemezse hata mesajı gösterilir
        if not success:
            return self.show_msg("Error", msg, "warning")

        # Atanan teknisyene bildirim gönderilir
        self.add_notification_for_user(
            technician,
            "New Repair Request",
            f"{self.current_user} assigned a new repair request to you."
        )

        # Müşteriye kayıt oluşturuldu bildirimi gönderilir
        self.add_notification_for_user(
            self.current_user,
            "Repair Request Created",
            "Your repair request was created successfully."
        )

        # Kayıt oluşturma işlemi loglanır
        self.logger.log_action(
            f"{self.current_user} created a new repair request. Serial No: {serial_no}"
        )

        # Başarı mesajı gösterilir
        self.show_msg("Success", msg, "info")

        # Form alanları temizlenir
        self.clear_customer_form()

        # Ana sayfa güncellenir
        self.show_home_page()

    # Müşterinin Pending durumundaki kayıt için teknisyen değiştirmesini sağlar.
    def change_technician(self):

        # Tablodan seçilen kayıt alınır
        item = self.get_selected_item()

        if not item:
            return

        # Seçilen kaydın bilgileri alınır
        repair_id = item[0]
        current_status = item[6]
        current_technician = item[2]

        # Teknisyen değiştirme işlemini sadece müşteri yapabilir
        if self.user_role != "Customer":
            return self.show_msg("Error", "Only the customer can change the technician.", "warning")

        # Teknisyen sadece Pending aşamasında değiştirilebilir
        if current_status != "Pending":
            return self.show_msg(
                "Error",
                self.get_technician_change_error_message(current_status),
                "warning"
            )

        # Sistemde kayıtlı teknisyenler alınır
        techs = self.db.get_users_by_role("Technician")

        # Kayıtlı teknisyen yoksa hata verir
        if not techs:
            return self.show_msg("Error", "There is no registered technician in the system.", "warning")

        # Teknisyen değiştirme penceresi oluşturulur
        win = ctk.CTkToplevel(self)
        win.title("Change Technician")
        win.geometry("360x220")
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        # Başlık
        ctk.CTkLabel(
            win,
            text="Select a new technician",
            font=("Arial", 17, "bold")
        ).pack(pady=20)

        # Yeni teknisyen seçme kutusu
        combo = ctk.CTkComboBox(win, values=techs, width=240)
        combo.pack(pady=8)
        combo.set(current_technician)

        # Teknisyen değişikliğini kaydeden iç fonksiyon
        def save_change():

            # Seçilen yeni teknisyen alınır
            new_technician = combo.get()

            # Aynı teknisyen seçildiyse işlem yapılmaz
            if new_technician == current_technician:
                return self.show_msg("Info", "This technician is already assigned.", "info", win)

            # Veritabanında teknisyen güncellenir
            success = self.db.update_technician(repair_id, new_technician)

            # Güncelleme başarılıysa bildirim ve log oluşturulur
            if success:
                self.add_notification_for_user(
                    new_technician,
                    "New Assignment",
                    f"Record #{repair_id} was assigned to you."
                )

                self.logger.log_action(
                    f"Record {repair_id} technician {current_technician} -> {new_technician} was changed."
                )

                self.show_msg("Success", "Technician changed successfully.", "info", win)
                win.destroy()
                self.show_home_page()

            # Güncelleme başarısızsa hata mesajı gösterilir
            else:
                self.show_msg(
                    "Error",
                    "Technician could not be changed. The record may not be Pending.",
                    "warning",
                    win
                )

        # Kaydet butonu
        ctk.CTkButton(
            win,
            text="Save",
            fg_color=self.primary_color,
            command=save_change
        ).pack(pady=18)

    # Seçilen tamir kaydının durumunu değiştirir.
    def change_status(self, new_status):

        # Tablodan seçilen kayıt alınır
        item = self.get_selected_item()

        if not item:
            return

        # Kayıt bilgileri alınır
        repair_id = item[0]
        customer_name = item[1]
        technician_name = item[2]
        current_status = item[6]

        # Müşteri sadece teklif onaylama veya reddetme işlemi yapabilir
        if self.user_role == "Customer":
            if new_status not in ["Repairing", "Rejected"]:
                return self.show_msg("Error", "The customer cannot make this status change.", "warning")

            # Reddedilmiş kayıt tekrar değiştirilemez
            if current_status == "Rejected":
                return self.show_msg(
                    "Error",
                    "This offer has already been rejected. The status cannot be changed again.",
                    "warning"
                )

            # Tamamlanmış kayıt tekrar değiştirilemez
            if current_status == "Completed":
                return self.show_msg(
                    "Error",
                    "This repair has already been completed. The status cannot be changed again.",
                    "warning"
                )

            # Müşteri sadece Waiting Approval durumunda onay veya red verebilir
            if current_status != "Waiting Approval":
                return self.show_msg(
                    "Error",
                    "You can only approve or reject the offer when the status is Waiting Approval.",
                    "warning"
                )

        # Teknisyen için durum geçiş kontrolleri
        if self.user_role == "Technician":

            # Teknisyen sadece Pending kaydı Diagnosing yapabilir
            if new_status == "Diagnosing" and current_status != "Pending":
                if current_status == "Rejected":
                    return self.show_msg(
                        "Error",
                        "This record was rejected. It cannot be taken into diagnosis.",
                        "warning"
                    )

                if current_status == "Completed":
                    return self.show_msg(
                        "Error",
                        "This record is already completed. It cannot be taken into diagnosis again.",
                        "warning"
                    )

                return self.show_msg(
                    "Error",
                    "Only Pending records can be taken into diagnosis.",
                    "warning"
                )

            # Teknisyen sadece Repairing durumundaki kaydı Completed yapabilir
            if new_status == "Completed" and current_status != "Repairing":
                if current_status == "Rejected":
                    return self.show_msg(
                        "Error",
                        "This record was rejected. It cannot be completed.",
                        "warning"
                    )

                if current_status == "Pending":
                    return self.show_msg(
                        "Error",
                        "This record has not been diagnosed yet. It cannot be completed.",
                        "warning"
                    )

                if current_status == "Diagnosing":
                    return self.show_msg(
                        "Error",
                        "The master has not created an offer yet. This record cannot be completed.",
                        "warning"
                    )

                if current_status == "Waiting Approval":
                    return self.show_msg(
                        "Error",
                        "The customer has not approved the offer yet. This record cannot be completed.",
                        "warning"
                    )

                return self.show_msg(
                    "Error",
                    "Only Repairing records can be completed.",
                    "warning"
                )

        # Completed veya Rejected kayıtlar tekrar değiştirilemez
        if current_status in ["Completed", "Rejected"]:
            return self.show_msg(
                "Error",
                f"{current_status} records cannot be changed again.",
                "warning"
            )

        # StatusManager ile geçerli durum geçişi kontrol edilir
        if not StatusManager.is_valid_transition(current_status, new_status):
            return self.show_msg(
                "Error",
                f"This record is currently '{current_status}', so it cannot be changed to '{new_status}'.",
                "error"
            )

        # Müşteri teklif onayı veya reddi yaparken özel onay penceresi açılır
        if self.user_role == "Customer" and new_status in ["Repairing", "Rejected"]:
            action_title = "APPROVE OFFER" if new_status == "Repairing" else "REJECT OFFER"
            action_message = (
                "Do you want to approve this offer and start the repair process?"
                if new_status == "Repairing"
                else "Do you want to reject this offer? This action cannot be changed later."
            )

            action_button_text = "Approve Offer" if new_status == "Repairing" else "Reject Offer"
            action_button_color = self.primary_color if new_status == "Repairing" else "#e74c3c"
            action_hover_color = self.get_hover_color() if new_status == "Repairing" else "#c0392b"

            # Onay penceresi
            win = ctk.CTkToplevel(self)
            win.title(action_title)
            win.geometry("520x420")
            win.resizable(False, False)
            win.lift()
            win.focus_force()
            win.attributes("-topmost", True)
            win.grab_set()

            # Ana kart
            main_card = ctk.CTkFrame(win, corner_radius=24)
            main_card.pack(fill="both", expand=True, padx=24, pady=24)

            # İşlem başlığı
            ctk.CTkLabel(
                main_card,
                text=action_title,
                font=("Arial", 24, "bold"),
                text_color=action_button_color
            ).pack(pady=(26, 6))

            # İşlem açıklaması
            ctk.CTkLabel(
                main_card,
                text=action_message,
                wraplength=400,
                justify="center",
                font=("Arial", 14),
                text_color=self.get_sub_text_color()
            ).pack(pady=(0, 20))

            # Bilgi kartı
            info_card = ctk.CTkFrame(main_card, corner_radius=18)
            info_card.pack(fill="x", padx=28, pady=8)

            # Onay ekranında gösterilecek bilgiler
            rows = [
                ("Record ID", repair_id),
                ("Customer", customer_name),
                ("Technician", technician_name),
                ("Current Status", current_status),
                ("New Status", new_status)
            ]

            # Bilgiler ekrana yerleştirilir
            for label, value in rows:
                row = ctk.CTkFrame(info_card, fg_color="transparent")
                row.pack(fill="x", padx=18, pady=5)

                ctk.CTkLabel(
                    row,
                    text=label + ":",
                    font=("Arial", 13, "bold"),
                    width=130,
                    anchor="w"
                ).pack(side="left")

                ctk.CTkLabel(
                    row,
                    text=str(value),
                    font=("Arial", 13),
                    anchor="w"
                ).pack(side="left")

            # Buton alanı
            button_frame = ctk.CTkFrame(main_card, fg_color="transparent")
            button_frame.pack(pady=(22, 14))

            # Durum değişikliğini onaylayan iç fonksiyon
            def confirm_status_change():

                # Veritabanında durum güncellenir
                self.db.update_status(repair_id, new_status)

                # Müşteriye durum bildirimi gönderilir
                self.add_notification_for_user(
                    customer_name,
                    "Status Updated",
                    f"Your record #{repair_id} status is now {new_status}."
                )

                # Teknisyene durum bildirimi gönderilir
                self.add_notification_for_user(
                    technician_name,
                    "Status Updated",
                    f"Record #{repair_id} status is now {new_status}."
                )

                # Durum değişikliği loglanır
                self.logger.log_action(
                    f"Record {repair_id} status {current_status} -> {new_status} was updated."
                )

                # Pencere kapatılır ve ana sayfa yenilenir
                win.destroy()
                self.show_home_page()

            # Onay / red butonu
            ctk.CTkButton(
                button_frame,
                text=action_button_text,
                width=150,
                height=38,
                fg_color=action_button_color,
                hover_color=action_hover_color,
                command=confirm_status_change
            ).pack(side="left", padx=8)

            # İptal butonu
            ctk.CTkButton(
                button_frame,
                text="Cancel",
                width=120,
                height=38,
                fg_color=self.get_secondary_button_color(),
                hover_color=self.get_hover_color(),
                text_color=self.get_text_color(),
                command=win.destroy
            ).pack(side="left", padx=8)

            return

        # Diğer geçerli durum değişiklikleri doğrudan güncellenir
        self.db.update_status(repair_id, new_status)

        # Müşteriye bildirim gönderilir
        self.add_notification_for_user(
            customer_name,
            "Status Updated",
            f"Your record #{repair_id} status is now {new_status}."
        )

        # Teknisyene bildirim gönderilir
        self.add_notification_for_user(
            technician_name,
            "Status Updated",
            f"Record #{repair_id} status is now {new_status}."
        )

        # Durum değişikliği loglanır
        self.logger.log_action(
            f"Record {repair_id} status {current_status} -> {new_status} was updated."
        )

        # Ana sayfa yenilenir
        self.show_home_page()

    # Usta tarafından tamir kaydı için fiyat ve süre teklifi oluşturur.
    def usta_offer(self):

        # Tablodan seçilen kayıt alınır
        item = self.get_selected_item()

        if not item:
            return

        # Kayıt bilgileri alınır
        repair_id = item[0]
        customer_name = item[1]
        technician_name = item[2]
        current_status = item[6]

        # Reddedilen kayda teklif verilemez
        if current_status == "Rejected":
            return self.show_msg(
                "Error",
                "An offer cannot be created because this repair request was rejected.",
                "warning"
            )

        # Tamamlanmış kayda teklif verilemez
        if current_status == "Completed":
            return self.show_msg(
                "Error",
                "An offer cannot be created because this repair has already been completed.",
                "warning"
            )

        # Daha önce teklif oluşturulmuşsa tekrar teklif verilmez
        if current_status == "Waiting Approval":
            return self.show_msg(
                "Info",
                "An offer has already been created for this record. It is waiting for customer approval.",
                "info"
            )

        # Onaylanmış teklif tekrar oluşturulmaz
        if current_status == "Repairing":
            return self.show_msg(
                "Info",
                "The offer has already been approved and the repair is in progress.",
                "info"
            )

        # Teklif sadece Diagnosing aşamasında oluşturulabilir
        if current_status != "Diagnosing":
            return self.show_msg(
                "Error",
                "To create an offer, the record must first be moved to Diagnosing by the technician.",
                "warning"
            )

        # Teklif oluşturma penceresi
        win = ctk.CTkToplevel(self)
        win.title("Create Offer")
        win.geometry("520x470")
        win.resizable(False, False)
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)
        win.grab_set()

        # Ana kart
        main_card = ctk.CTkFrame(win, corner_radius=24)
        main_card.pack(fill="both", expand=True, padx=24, pady=24)

        # Başlık
        ctk.CTkLabel(
            main_card,
            text="CREATE OFFER",
            font=("Arial", 24, "bold"),
            text_color=self.primary_color
        ).pack(pady=(26, 6))

        # Kayıt numarası bilgisi
        ctk.CTkLabel(
            main_card,
            text=f"Record #{repair_id}",
            font=("Arial", 13),
            text_color=self.get_sub_text_color()
        ).pack(pady=(0, 18))

        # Form kartı
        form_card = ctk.CTkFrame(main_card, corner_radius=18)
        form_card.pack(fill="x", padx=28, pady=10)

        # Fiyat etiketi
        ctk.CTkLabel(
            form_card,
            text="Offer Price (TL)",
            font=("Arial", 13, "bold"),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(18, 5))

        # Fiyat giriş alanı
        price_entry = ctk.CTkEntry(
            form_card,
            placeholder_text="Example: 1200",
            height=38
        )
        price_entry.pack(fill="x", padx=20, pady=(0, 14))

        # Tahmini süre etiketi
        ctk.CTkLabel(
            form_card,
            text="Estimated Repair Time",
            font=("Arial", 13, "bold"),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(2, 5))

        # Süre giriş satırı
        time_row = ctk.CTkFrame(form_card, fg_color="transparent")
        time_row.pack(fill="x", padx=20, pady=(0, 8))

        # Süre sayı alanı
        time_number_entry = ctk.CTkEntry(
            time_row,
            placeholder_text="Number",
            height=38,
            width=170
        )
        time_number_entry.pack(side="left", padx=(0, 10))

        # Süre birimi seçimi
        time_unit_box = ctk.CTkComboBox(
            time_row,
            values=["day(s)", "week(s)"],
            height=38,
            width=170,
            state="readonly"
        )
        time_unit_box.pack(side="left")
        time_unit_box.set("day(s)")

        # Bilgilendirme yazısı
        ctk.CTkLabel(
            form_card,
            text="You must enter a number and select a time unit.",
            font=("Arial", 12),
            text_color=self.get_sub_text_color()
        ).pack(anchor="w", padx=20, pady=(0, 18))

        # Buton alanı
        button_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        button_frame.pack(pady=(18, 12))

        # Teklifi kaydeden iç fonksiyon
        def save_offer():

            # Kullanıcının girdiği değerler alınır
            price_text = price_entry.get().strip()
            time_number_text = time_number_entry.get().strip()
            time_unit = time_unit_box.get().strip()

            # Fiyat numeric olmalıdır
            try:
                price = float(price_text)
            except ValueError:
                return self.show_msg(
                    "Error",
                    "Offer price must be numeric.",
                    "warning",
                    win
                )

            # Fiyat sıfır veya negatif olamaz
            if price <= 0:
                return self.show_msg(
                    "Error",
                    "Offer price cannot be zero or negative.",
                    "warning",
                    win
                )

            # Tahmini süre boş olamaz
            if not time_number_text:
                return self.show_msg(
                    "Error",
                    "Estimated repair time number cannot be empty.",
                    "warning",
                    win
                )

            # Tahmini süre pozitif tam sayı olmalıdır
            if not time_number_text.isdigit():
                return self.show_msg(
                    "Error",
                    "Estimated repair time must be a positive whole number.",
                    "warning",
                    win
                )

            # Süre sayıya çevrilir
            time_number = int(time_number_text)

            # Süre sıfır veya negatif olamaz
            if time_number <= 0:
                return self.show_msg(
                    "Error",
                    "Estimated repair time must be greater than 0.",
                    "warning",
                    win
                )

            # Geçerli süre birimi kontrol edilir
            if time_unit not in ["day(s)", "week(s)"]:
                return self.show_msg(
                    "Error",
                    "Please select a valid time unit.",
                    "warning",
                    win
                )

            # Tahmini süre metni oluşturulur
            estimated_time = f"{time_number} {time_unit}"

            # Kayıt Waiting Approval durumuna alınır ve teklif bilgileri kaydedilir
            self.db.update_status(repair_id, "Waiting Approval", price, estimated_time)

            # Müşteriye teklif bildirimi gönderilir
            self.add_notification_for_user(
                customer_name,
                "Offer Created",
                f"An offer of {price} TL was created for your record #{repair_id}."
            )

            # Teknisyene teklif bildirimi gönderilir
            self.add_notification_for_user(
                technician_name,
                "Offer Created",
                f"An offer was created for record #{repair_id}."
            )

            # Ustaya işlem bildirimi gönderilir
            self.add_notification_for_user(
                self.current_user,
                "Offer Created",
                f"You created an offer for record #{repair_id}."
            )

            # Teklif oluşturma işlemi loglanır
            self.logger.log_action(
                f"Record {repair_id} offer was created. Price: {price} TL"
            )

            # Başarı mesajı gösterilir
            self.show_msg(
                "Success",
                "Price and estimated time offer created.",
                "info",
                win
            )

            # Pencere kapatılır ve ana sayfa yenilenir
            win.destroy()
            self.show_home_page()

        # Teklif oluşturma butonu
        ctk.CTkButton(
            button_frame,
            text="Create Offer",
            width=150,
            height=38,
            fg_color=self.primary_color,
            command=save_offer
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

    # Seçilen tamir kaydını kurallara göre siler.
    def del_rep(self):

        # Tablodan seçilen kayıt alınır
        item = self.get_selected_item()

        if not item:
            return

        # Silme için gerekli bilgiler alınır
        repair_id = item[0]
        status = item[6]
        payment_status = item[9]

        # Rejected kayıt silinebilir
        if status == "Rejected":
            if self.ask_yes_no(
                "Confirmation",
                "This record was rejected, so it can be deleted. Do you want to delete it?"
            ):
                self.db.delete_repair(repair_id)
                self.logger.log_action(f"Record {repair_id} was deleted.")
                self.show_home_page()
            return

        # Ödemesi yapılmış kayıt silinebilir
        if payment_status == "Paid":
            if self.ask_yes_no(
                "Confirmation",
                "Payment for this record has been completed. Do you want to delete it?"
            ):
                self.db.delete_repair(repair_id)
                self.logger.log_action(f"Record {repair_id} was deleted.")
                self.show_home_page()
            return

        # Tamamlanmış ama ödenmemiş kayıt silinemez
        if status == "Completed" and payment_status != "Paid":
            return self.show_msg(
                "Error",
                "This record is completed, but payment has not been made. Therefore, it cannot be deleted.",
                "warning"
            )

        # Aktif süreçteki kayıtlar silinemez
        self.show_msg(
            "Error",
            "This record is still in an active process, so it cannot be deleted.",
            "warning"
        )

    # Ana sayfadaki tabloyu veritabanındaki güncel bilgilerle doldurur.
    def load_table(self):

        # Tablodaki eski satırları temizler
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Kullanıcı rolüne göre verileri çekip tabloya ekler
        for row in self.db.get_data(self.user_role, self.current_user):
            self.tree.insert("", "end", values=row)