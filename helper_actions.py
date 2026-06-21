import customtkinter as ctk

from helpers import SystemSettings


# Yardımcı işlemleri yöneten sınıf.
# Form temizleme, duruma göre hata mesajı üretme
# ve sistem ayarlarını açma işlemleri burada tutulur.
class HelperActions:

    # Yeni arıza kaydı formundaki giriş alanlarını temizler.
    def clear_customer_form(self):

        # Cihaz modeli alanı varsa içeriğini temizler
        if hasattr(self, "e_dev"):
            self.e_dev.delete(0, "end")

        # Seri numarası alanı varsa içeriğini temizler
        if hasattr(self, "e_serial"):
            self.e_serial.delete(0, "end")

        # Hasar açıklaması alanı varsa içeriğini temizler
        if hasattr(self, "e_dmg"):
            self.e_dmg.delete(0, "end")

    # Ödeme yapılamayan durumlarda kullanıcıya uygun hata mesajı döndürür.
    def get_payment_error_message(self, status):

        # Reddedilen kayıt için ödeme yapılamaz
        if status == "Rejected":
            return "Payment cannot be made because this repair request was rejected."

        # Pending durumunda teknisyen henüz işleme başlamamıştır
        if status == "Pending":
            return "Payment cannot be made because the technician has not started diagnosis yet."

        # Diagnosing durumunda henüz teklif oluşturulmamıştır
        if status == "Diagnosing":
            return "Payment cannot be made because the master has not created an offer yet."

        # Waiting Approval durumunda müşteri önce teklifi onaylamalıdır
        if status == "Waiting Approval":
            return "You must approve the offer first."

        # Repairing durumunda tamir hâlâ devam etmektedir
        if status == "Repairing":
            return "Payment cannot be made because the repair is still in progress."

        # Diğer geçersiz durumlar için genel hata mesajı
        return "Payment cannot be made for the current status."

    # Feedback verilemeyen durumlarda kullanıcıya uygun hata mesajı döndürür.
    def get_feedback_error_message(self, status):

        # Reddedilen kayıt için feedback verilemez
        if status == "Rejected":
            return "Feedback cannot be given because this repair request was rejected."

        # Pending durumunda işlem başlamadığı için feedback verilemez
        if status == "Pending":
            return "Feedback cannot be given because the technician has not started diagnosis yet."

        # Diagnosing durumunda tamir hâlâ incelenmektedir
        if status == "Diagnosing":
            return "Feedback cannot be given because the repair is still being diagnosed."

        # Waiting Approval durumunda teklif henüz onaylanmamıştır
        if status == "Waiting Approval":
            return "Feedback cannot be given because the offer has not been approved yet."

        # Repairing durumunda tamir tamamlanmamıştır
        if status == "Repairing":
            return "Feedback cannot be given because the repair is still in progress."

        # Feedback için tamirin tamamlanmış olması gerekir
        return "The repair must be completed before feedback can be given."

    # Teknisyen değiştirilemeyen durumlarda uygun hata mesajı döndürür.
    def get_technician_change_error_message(self, status):

        # Reddedilen kayıt için teknisyen değiştirilemez
        if status == "Rejected":
            return "The technician cannot be changed because this repair request was rejected."

        # Diagnosis başladıktan sonra teknisyen değiştirilemez
        if status == "Diagnosing":
            return "The technician cannot be changed because diagnosis has already started."

        # Teklif oluşturulduktan sonra teknisyen değiştirilemez
        if status == "Waiting Approval":
            return "The technician cannot be changed because an offer has already been created."

        # Tamir başladıktan sonra teknisyen değiştirilemez
        if status == "Repairing":
            return "The technician cannot be changed because the repair is already in progress."

        # Tamir tamamlandıktan sonra teknisyen değiştirilemez
        if status == "Completed":
            return "The technician cannot be changed because the repair has already been completed."

        # Teknisyen yalnızca Pending aşamasında değiştirilebilir
        return "The technician can only be changed while the record is Pending."

    # ---------------- REPAIR ACTIONS ----------------

    # Sistem ayarları penceresini açar.
    # Kullanıcı tema ve tema rengi seçebilir.
    def open_settings(self):

        # Ayarlar için yeni pencere oluşturulur
        win = ctk.CTkToplevel(self)
        win.title("System Settings")
        win.geometry("360x300")
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        # Pencere başlığı
        ctk.CTkLabel(
            win,
            text="System Settings",
            font=("Arial", 20, "bold")
        ).pack(pady=18)

        # Tema seçimi için combobox
        theme_box = ctk.CTkComboBox(win, values=["Dark", "Light"], width=230)
        theme_box.pack(pady=8)
        theme_box.set(self.settings.theme)

        # Tema rengi seçimi için combobox
        color_box = ctk.CTkComboBox(win,
                                    values=["Blue", "Green", "Dark Blue", "Purple", "Orange", "Red", "Teal", "Pink"],
                                    width=230)
        color_box.pack(pady=8)
        color_box.set(self.settings.theme_color)

        # Seçilen ayarları kaydeden iç fonksiyon
        def save_settings():

            # Yeni ayarlar SystemSettings nesnesi olarak tutulur
            self.settings = SystemSettings(theme_box.get(), color_box.get())

            # Ayarlar veritabanında güncellenir
            self.db.update_settings(self.settings)

            # Uygulamanın görünüm modu güncellenir
            ctk.set_appearance_mode(self.settings.theme)

            # CustomTkinter tema rengi güncellenir
            ctk.set_default_color_theme(self.get_ctk_theme_name(self.settings.theme_color))

            # Ana renk yeniden hesaplanır
            self.primary_color = self.get_primary_color()

            # Başarı mesajı gösterilir
            self.show_msg(
                "Success",
                "Settings saved successfully.",
                "info",
                win
            )

            # Ayarlar penceresi kapatılır
            win.destroy()

            # Dashboard yeni ayarlara göre tekrar yüklenir
            self.show_dashboard()

        # Ayarları kaydetme butonu
        ctk.CTkButton(
            win,
            text="Save",
            width=230,
            fg_color=self.primary_color,
            command=save_settings
        ).pack(pady=18)