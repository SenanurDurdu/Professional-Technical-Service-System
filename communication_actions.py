import customtkinter as ctk
from tkinter import simpledialog

from models import Message, NotificationDetail


# Mesajlaşma ve bildirim işlemlerini yöneten action sınıfı.
# Kullanıcılar arasında mesaj gönderme, bildirim oluşturma
# ve gelen mesaj/bildirimleri görüntüleme işlemlerini içerir.
class CommunicationActions:

    # Kullanıcının başka bir kullanıcıya mesaj göndermesini sağlar.
    def send_message(self):

        # Mevcut kullanıcı dışındaki tüm kullanıcıları getirir
        users = self.db.get_all_usernames_except(self.current_user)

        # Gönderilecek kullanıcı yoksa hata verir
        if not users:
            return self.show_msg(
                "Error",
                "There is no other registered user to send a message.",
                "warning"
            )

        # Mesaj gönderme penceresi
        win = ctk.CTkToplevel(self)
        win.title("Send Message")
        win.geometry("460x430")
        win.resizable(False, False)
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        # Ana kart alanı
        card = ctk.CTkFrame(win, corner_radius=18)
        card.pack(fill="both", expand=True, padx=22, pady=22)

        # Başlık
        ctk.CTkLabel(
            card,
            text="Send Message",
            font=("Arial", 22, "bold")
        ).pack(anchor="w", padx=18, pady=(18, 14))

        # Alıcı etiketi
        ctk.CTkLabel(
            card,
            text="Receiver",
            font=("Arial", 13, "bold")
        ).pack(anchor="w", padx=18, pady=(0, 6))

        # Alıcı seçme kutusu
        receiver_box = ctk.CTkComboBox(
            card,
            values=users,
            width=340,
            height=36,
            state="readonly"
        )
        receiver_box.pack(anchor="w", padx=18, pady=(0, 18))
        receiver_box.set(users[0])

        # Mesaj etiketi
        ctk.CTkLabel(
            card,
            text="Message",
            font=("Arial", 13, "bold")
        ).pack(anchor="w", padx=18, pady=(0, 6))

        # Mesaj yazma alanı
        msg_box = ctk.CTkTextbox(
            card,
            width=340,
            height=150,
            corner_radius=12
        )
        msg_box.pack(anchor="w", padx=18, pady=(0, 18))

        # Buton alanı
        button_frame = ctk.CTkFrame(card, fg_color="transparent")
        button_frame.pack(pady=(8, 10))

        # Mesajı kaydeden iç fonksiyon
        def save_message():

            # Kullanıcının seçtiği alıcı ve yazdığı mesaj
            receiver = receiver_box.get()
            content = msg_box.get("0.0", "end").strip()

            # Alanlar boş bırakılamaz
            if not receiver or not content:
                return self.show_msg(
                    "Error",
                    "Receiver and message cannot be empty.",
                    "warning",
                    win
                )

            # Message nesnesi oluşturulur
            message = Message(self.current_user, receiver, content)

            # Veritabanına kaydedilir
            self.db.add_message(message)

            # Alıcı kullanıcıya bildirim gönderilir
            self.add_notification_for_user(
                receiver,
                "New Message",
                f"{self.current_user} sent you a message."
            )

            # Log kaydı oluşturulur
            self.logger.log_action(
                f"{self.current_user} sent a message to {receiver}."
            )

            # Başarı mesajı
            self.show_msg("Success", "Message sent successfully.", "info", win)

            # Pencere kapatılır
            win.destroy()

        # Mesaj gönderme butonu
        ctk.CTkButton(
            button_frame,
            text="Send Message",
            width=130,
            height=34,
            fg_color=self.primary_color,
            command=save_message
        ).pack(side="left", padx=8)

        # İptal butonu
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=130,
            height=34,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=win.destroy
        ).pack(side="left", padx=8)

    # Kullanıcının mesajlarını görüntüler.
    def show_messages(self):

        # Veritabanından mesajları çeker
        rows = self.db.get_messages(self.current_user)

        # Temaya göre kart rengi belirler
        def card_color():
            return "#f1f1f1" if self.settings.theme == "Light" else "#303030"

        # Mesaj görüntüleme penceresi
        win = ctk.CTkToplevel(self)
        win.title("My Messages")
        win.geometry("640x520")
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        # Ana container
        container = ctk.CTkFrame(win, corner_radius=18)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Başlık
        ctk.CTkLabel(
            container,
            text="My Messages",
            font=("Arial", 22, "bold")
        ).pack(anchor="w", padx=18, pady=(16, 6))

        # Scrollable alan
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=14, pady=(4, 16))

        # Mesaj yoksa bilgi verir
        if not rows:

            ctk.CTkLabel(
                scroll,
                text="No messages found.",
                font=("Arial", 14),
                text_color=self.get_sub_text_color()
            ).pack(pady=30)

            return

        # Her mesaj için kart oluşturur
        for sender, receiver, content, date in rows:

            msg = Message(sender, receiver, content, date)

            # Mesajın mevcut kullanıcıya ait olup olmadığını kontrol eder
            is_mine = msg.sender == self.current_user

            # Mesaj balon renkleri
            bubble_color = self.primary_color if is_mine else card_color()
            text_color = "white" if is_mine else self.get_text_color()
            anchor_side = "e" if is_mine else "w"

            # Mesaj kartı
            card = ctk.CTkFrame(scroll, corner_radius=14, fg_color=bubble_color)
            card.pack(anchor=anchor_side, fill="x", padx=8, pady=7)

            # Başlık bilgisi
            header_text = "To: " + msg.receiver if is_mine else "From: " + msg.sender

            ctk.CTkLabel(
                card,
                text=header_text,
                font=("Arial", 13, "bold"),
                text_color=text_color
            ).pack(anchor="w", padx=14, pady=(10, 2))

            # Mesaj içeriği
            ctk.CTkLabel(
                card,
                text=msg.content,
                font=("Arial", 13),
                text_color=text_color,
                wraplength=520,
                justify="left"
            ).pack(anchor="w", padx=14, pady=4)

            # Mesaj tarihi
            ctk.CTkLabel(
                card,
                text=msg.date,
                font=("Arial", 11),
                text_color=text_color
            ).pack(anchor="e", padx=14, pady=(0, 10))

    # Sisteme bildirim gönderir.
    def create_notification(self):

        # Kullanıcı listesini getirir
        users = self.db.get_all_usernames_except(self.current_user)

        # Kullanıcı yoksa hata verir
        if not users:
            return self.show_msg(
                "Error",
                "There is no registered user to send a notification.",
                "warning"
            )

        # Bildirim oluşturma penceresi
        win = ctk.CTkToplevel(self)
        win.title("Send Notification")
        win.geometry("520x590")
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
            text="SEND NOTIFICATION",
            font=("Arial", 24, "bold"),
            text_color=self.primary_color
        ).pack(pady=(26, 6))

        # Açıklama yazısı
        ctk.CTkLabel(
            main_card,
            text="Create and send a system notification",
            font=("Arial", 13),
            text_color=self.get_sub_text_color()
        ).pack(pady=(0, 18))

        # Form alanı
        form_card = ctk.CTkFrame(main_card, corner_radius=18)
        form_card.pack(fill="x", padx=28, pady=10)

        # Receiver etiketi
        ctk.CTkLabel(
            form_card,
            text="Receiver",
            font=("Arial", 13, "bold"),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(18, 5))

        # Kullanıcı seçme kutusu
        receiver_box = ctk.CTkComboBox(
            form_card,
            values=users,
            height=38,
            state="readonly"
        )
        receiver_box.pack(fill="x", padx=20, pady=(0, 14))
        receiver_box.set(users[0])

        # Başlık etiketi
        ctk.CTkLabel(
            form_card,
            text="Notification Title",
            font=("Arial", 13, "bold"),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(2, 5))

        # Bildirim başlığı giriş alanı
        title_entry = ctk.CTkEntry(
            form_card,
            placeholder_text="Enter notification title",
            height=38
        )
        title_entry.pack(fill="x", padx=20, pady=(0, 14))

        # Mesaj etiketi
        ctk.CTkLabel(
            form_card,
            text="Notification Message",
            font=("Arial", 13, "bold"),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(2, 5))

        # Bildirim mesaj alanı
        message_box = ctk.CTkTextbox(
            form_card,
            height=120,
            corner_radius=12
        )
        message_box.pack(fill="x", padx=20, pady=(0, 18))

        # Buton alanı
        button_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        button_frame.pack(pady=(18, 12))

        # Bildirimi gönderen iç fonksiyon
        def send_notification():

            recipient = receiver_box.get().strip()
            title = title_entry.get().strip()
            message = message_box.get("0.0", "end").strip()

            # Alanlar boş bırakılamaz
            if not recipient or not title or not message:
                return self.show_msg(
                    "Error",
                    "Receiver, title, and message cannot be empty.",
                    "warning",
                    win
                )

            # Kullanıcı sistemde kayıtlı mı kontrol edilir
            if not self.db.user_exists(recipient):
                return self.show_msg(
                    "Error",
                    "The notification receiver is not registered in the system.",
                    "warning",
                    win
                )

            # Notification nesnesi oluşturulur
            notification = NotificationDetail(title, message, recipient)

            # Bildirim sisteme eklenir
            self.notification_system.add_notification(notification.message)
            self.db.add_notification(notification)

            # Bildirimi gönderen kullanıcıya bilgi bildirimi gönderilir
            self.add_notification_for_user(
                self.current_user,
                "Notification Sent",
                f"You sent a notification to {recipient}."
            )

            # Log kaydı
            self.logger.log_action(
                f"{self.current_user} sent a notification to {recipient}."
            )

            # Başarı mesajı
            self.show_msg(
                "Success",
                "Notification sent successfully.",
                "info",
                win
            )

            # Pencere kapatılır
            win.destroy()

        # Gönder butonu
        ctk.CTkButton(
            button_frame,
            text="Send Notification",
            width=160,
            height=38,
            fg_color=self.primary_color,
            command=send_notification
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

    # Kullanıcının bildirimlerini görüntüler.
    def show_notifications(self):

        # Veritabanından bildirimleri alır
        rows = self.db.get_notifications(self.current_user)

        # Normal kart rengi
        def card_color():
            return "#f1f1f1" if self.settings.theme == "Light" else "#303030"

        # Okunmamış bildirim rengi
        def unread_card_color():
            return "#e8f3ff" if self.settings.theme == "Light" else "#1f3b52"

        # Bildirim ekranı
        win = ctk.CTkToplevel(self)
        win.title("My Notifications")
        win.geometry("640x520")
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        # Ana container
        container = ctk.CTkFrame(win, corner_radius=18)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Başlık
        ctk.CTkLabel(
            container,
            text="My Notifications",
            font=("Arial", 22, "bold")
        ).pack(anchor="w", padx=18, pady=(16, 6))

        # Scrollable alan
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=14, pady=(4, 16))

        # Bildirim yoksa bilgi verir
        if not rows:

            ctk.CTkLabel(
                scroll,
                text="No notifications.",
                font=("Arial", 14),
                text_color=self.get_sub_text_color()
            ).pack(pady=30)

            return

        unread_ids = []

        # Bildirim kartlarını oluşturur
        for notification_id, title, message, date, is_read in rows:

            notification = NotificationDetail(
                title,
                message,
                self.current_user,
                date,
                is_read,
                notification_id
            )

            # Okunmamış bildirimleri listeye ekler
            if notification.is_read == 0:
                unread_ids.append(notification.notification_id)

            # Bildirim kart rengini belirler
            notification_card_color = unread_card_color() if notification.is_read == 0 else card_color()

            # NEW etiketi sadece okunmamış bildirimlerde görünür
            status_text = "NEW" if notification.is_read == 0 else ""

            # Bildirim kartı
            card = ctk.CTkFrame(scroll, corner_radius=14, fg_color=notification_card_color)
            card.pack(fill="x", padx=8, pady=7)

            # Üst satır
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=14, pady=(10, 2))

            # Bildirim başlığı
            ctk.CTkLabel(
                top_row,
                text=notification.title,
                font=("Arial", 14, "bold"),
                text_color=self.get_text_color()
            ).pack(side="left")

            # NEW etiketi
            if status_text:
                ctk.CTkLabel(
                    top_row,
                    text=status_text,
                    font=("Arial", 11, "bold"),
                    text_color=self.primary_color
                ).pack(side="right")

            # Bildirim mesajı
            ctk.CTkLabel(
                card,
                text=notification.message,
                font=("Arial", 13),
                text_color=self.get_text_color(),
                wraplength=540,
                justify="left"
            ).pack(anchor="w", padx=14, pady=4)

            # Bildirim tarihi
            ctk.CTkLabel(
                card,
                text=notification.date,
                font=("Arial", 11),
                text_color=self.get_sub_text_color()
            ).pack(anchor="e", padx=14, pady=(0, 10))

        # Kullanıcı bildirim ekranını açtıktan sonra
        # tüm bildirimler okunmuş olarak işaretlenir.
        self.db.mark_notifications_as_read(self.current_user)