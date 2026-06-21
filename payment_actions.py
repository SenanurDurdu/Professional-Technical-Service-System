import customtkinter as ctk
from tkinter import simpledialog

from models import Payment, Feedback, Invoice
from helpers import DateHelper


# Ödeme, fatura ve feedback işlemlerini yöneten action sınıfı.
class PaymentActions:

    # Seçilen tamir kaydı için ödeme yapar.
    def pay_repair(self):

        # Tablodan seçilen kaydı alır
        item = self.get_selected_item()

        if not item:
            return

        # Seçilen kayıttan gerekli bilgileri alır
        repair_id = item[0]
        offer_price = float(item[7])
        status = item[6]
        payment_status = item[9]

        # Tamir tamamlanmadan ödeme yapılamaz
        if status != "Completed":
            return self.show_msg(
                "Error",
                self.get_payment_error_message(status),
                "warning"
            )

        # Aynı kayıt için ikinci kez ödeme yapılmasını engeller
        if payment_status == "Paid":
            return self.show_msg(
                "Info",
                "Payment has already been made for this record.",
                "info"
            )

        # Kullanılan parçaların toplam fiyatını hesaplar
        part_total = self.db.get_part_total(repair_id)

        # Toplam ödeme tutarı teklif fiyatı + parça toplamıdır
        total_amount = offer_price + part_total

        # Payment nesnesi oluşturulur ve ödenmiş olarak işaretlenir
        payment = Payment(total_amount)
        payment.mark_as_paid()

        # Ödeme bilgisi veritabanında güncellenir
        self.db.pay_repair(repair_id, payment.amount)

        # Ödeme sonrası fatura oluşturulur
        invoice = Invoice(repair_id, payment.amount)
        self.db.create_invoice(invoice, DateHelper.get_today())

        # Kullanıcıya ödeme bildirimi gönderilir
        self.add_notification_for_user(
            self.current_user,
            "Payment Completed",
            f"A payment of {total_amount} TL was made for record #{repair_id}."
        )

        # Ödeme işlemi loglanır
        self.logger.log_action(
            f"Record {repair_id} payment was made. Offer: {offer_price} TL, "
            f"Part: {part_total} TL, Total: {total_amount} TL"
        )

        # Başarı mesajı gösterilir
        self.show_msg(
            "Success",
            f"Payment completed.\n\n"
            f"Offer: {offer_price} TL\n"
            f"Spare Part Total: {part_total} TL\n"
            f"Grand Total: {total_amount} TL",
            "info"
        )

        # Ana sayfa güncellenir
        self.show_home_page()

    # Ödenmiş kayıt için fatura ekranını açar.
    def show_invoice(self):

        # Tablodan seçilen kaydı alır
        item = self.get_selected_item()

        if not item:
            return

        # Fatura için gerekli kayıt bilgilerini alır
        repair_id = item[0]
        customer_name = item[1]
        technician_name = item[2]
        device_model = item[3]
        serial_no = item[4]
        payment_status = item[9]

        # Ödeme yapılmamışsa fatura görüntülenemez
        if payment_status != "Paid":
            return self.show_msg(
                "Error",
                "No invoice was created because payment has not been made.",
                "warning"
            )

        # Veritabanından fatura bilgisi alınır
        invoice = self.db.get_invoice_by_repair(repair_id)

        # Fatura bulunamazsa hata verir
        if not invoice:
            return self.show_msg("Error", "No invoice was found for this record.", "warning")

        # Fatura ve teslim tarihi bilgileri alınır
        inv_repair_id, amount, invoice_date = invoice
        delivery_date = self.db.get_delivery_date_by_repair(repair_id)

        # Fatura penceresi oluşturulur
        win = ctk.CTkToplevel(self)
        win.title(f"Invoice - Record No {inv_repair_id}")
        win.geometry("560x700")
        win.resizable(False, False)
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        # Ana fatura kartı
        card = ctk.CTkFrame(win, corner_radius=22)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        # Fatura başlığı
        ctk.CTkLabel(
            card,
            text="TECHNICAL SERVICE INVOICE",
            font=("Arial", 24, "bold"),
            text_color=self.primary_color
        ).pack(pady=(25, 5))

        # Fatura tarihi
        ctk.CTkLabel(
            card,
            text=f"Invoice Date: {invoice_date}",
            font=("Arial", 13),
            text_color=self.get_sub_text_color()
        ).pack(pady=(0, 20))

        # Fatura detay alanı
        info_frame = ctk.CTkFrame(card, corner_radius=16)
        info_frame.pack(fill="x", padx=25, pady=10)

        # Faturada gösterilecek bilgiler
        rows = [
            ("Record ID", inv_repair_id),
            ("Customer", customer_name),
            ("Technician", technician_name),
            ("Device", device_model),
            ("Serial No / IMEI", serial_no),
            ("Delivery Date", delivery_date),
            ("Payment Status", "Paid")
        ]

        # Fatura detaylarını ekrana yerleştirir
        for label, value in rows:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=6)

            ctk.CTkLabel(
                row,
                text=label + ":",
                font=("Arial", 13, "bold"),
                width=150,
                anchor="w"
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=str(value),
                font=("Arial", 13),
                anchor="w"
            ).pack(side="left")

        # Toplam tutar alanı
        total_frame = ctk.CTkFrame(card, corner_radius=16, fg_color=self.primary_color)
        total_frame.pack(fill="x", padx=25, pady=(20, 10))

        # Toplam tutar başlığı
        ctk.CTkLabel(
            total_frame,
            text="TOTAL AMOUNT",
            font=("Arial", 15, "bold"),
            text_color="white"
        ).pack(pady=(16, 4))

        # Toplam tutar
        ctk.CTkLabel(
            total_frame,
            text=f"{amount} TL",
            font=("Arial", 30, "bold"),
            text_color="white"
        ).pack(pady=(0, 16))

        # Kapanış mesajı
        ctk.CTkLabel(
            card,
            text="Thank you for choosing our technical service.",
            font=("Arial", 13),
            text_color=self.get_sub_text_color()
        ).pack(pady=(15, 10))

        # Fatura penceresini kapatma butonu
        ctk.CTkButton(
            card,
            text="Close",
            width=180,
            height=36,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=win.destroy
        ).pack(pady=(10, 20))

    # Tamamlanmış tamir kaydı için feedback verir.
    def give_feedback(self):

        # Tablodan seçilen kaydı alır
        item = self.get_selected_item()

        if not item:
            return

        # Feedback için gerekli bilgiler
        repair_id = item[0]
        customer_name = item[1]
        status = item[6]

        # Sadece tamamlanmış kayıtlar için feedback verilebilir
        if status != "Completed":
            return self.show_msg(
                "Error",
                self.get_feedback_error_message(status),
                "warning"
            )

        # Aynı kayıt için daha önce feedback verilmiş mi kontrol eder
        existing_feedback = self.db.get_feedback_by_repair(repair_id)

        # Feedback varsa tekrar verilmesini engeller
        if existing_feedback:
            rating, comment = existing_feedback
            return self.show_msg(
                "Info",
                f"Feedback has already been given for this record.\n\n"
                f"Rating: {rating}/5\n"
                f"Comment: {comment}",
                "info"
            )

        # Kullanıcıdan 1-5 arası puan alır
        rating = simpledialog.askinteger(
            "Rating",
            "Enter a rating between 1 and 5:",
            minvalue=1,
            maxvalue=5,
            parent=self
        )

        # Kullanıcı iptal ederse işlem durur
        if rating is None:
            return

        # Kullanıcıdan yorum alır
        comment = simpledialog.askstring("Comment", "Write your comment:", parent=self)

        # Yorum boş olamaz
        if not comment:
            return self.show_msg("Error", "Comment cannot be empty.", "warning")

        # Feedback nesnesi oluşturulur
        feedback = Feedback(customer_name, rating, comment)

        # Feedback veritabanına kaydedilir
        success, msg = self.db.add_feedback(repair_id, feedback)

        # Sonuca göre mesaj gösterilir
        if success:
            self.logger.log_action(f"Record {repair_id} feedback was submitted.")
            self.show_msg("Success", msg, "info")
        else:
            self.show_msg("Error", msg, "warning")

    # Master kullanıcının tüm feedbackleri görüntülemesini sağlar.
    def show_all_feedbacks(self):

        # Tüm feedback kayıtlarını veritabanından alır
        rows = self.db.get_all_feedbacks()

        # Feedback penceresi oluşturulur
        win = ctk.CTkToplevel(self)
        win.title("Customer Feedbacks")
        win.geometry("680x560")
        win.resizable(False, False)
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        # Ana kart alanı
        main_card = ctk.CTkFrame(win, corner_radius=24)
        main_card.pack(fill="both", expand=True, padx=24, pady=24)

        # Başlık alanı
        header_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(22, 8))

        # Sol başlık alanı
        left_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_header.pack(side="left", anchor="w")

        # Sayfa başlığı
        ctk.CTkLabel(
            left_header,
            text="CUSTOMER FEEDBACKS",
            font=("Arial", 24, "bold"),
            text_color=self.primary_color
        ).pack(anchor="w")

        # Açıklama metni
        ctk.CTkLabel(
            left_header,
            text="Review customer ratings and service comments",
            font=("Arial", 13),
            text_color=self.get_sub_text_color()
        ).pack(anchor="w", pady=(4, 0))

        # Feedback sayısını gösterir
        ctk.CTkLabel(
            header_frame,
            text=f"{len(rows)} Feedback(s)",
            font=("Arial", 12, "bold"),
            text_color="white",
            fg_color=self.primary_color,
            corner_radius=14,
            padx=14,
            pady=6
        ).pack(side="right", anchor="ne")

        # Scrollable feedback alanı
        scroll = ctk.CTkScrollableFrame(main_card, corner_radius=18)
        scroll.pack(fill="both", expand=True, padx=24, pady=16)

        # Feedback yoksa boş ekran mesajı gösterir
        if not rows:
            empty_card = ctk.CTkFrame(scroll, corner_radius=18)
            empty_card.pack(fill="x", padx=12, pady=35)

            ctk.CTkLabel(
                empty_card,
                text="No Feedback Yet",
                font=("Arial", 18, "bold"),
                text_color=self.primary_color
            ).pack(pady=(28, 6))

            ctk.CTkLabel(
                empty_card,
                text="Customer feedbacks will appear here after completed repairs.",
                font=("Arial", 13),
                text_color=self.get_sub_text_color()
            ).pack(pady=(0, 28))

        else:

            # Her feedback için kart oluşturur
            for repair_id, customer, rating, comment in rows:
                feedback = Feedback(customer, rating, comment)

                feedback_card = ctk.CTkFrame(scroll, corner_radius=18)
                feedback_card.pack(fill="x", padx=12, pady=10)

                # Feedback kartının üst satırı
                top_row = ctk.CTkFrame(feedback_card, fg_color="transparent")
                top_row.pack(fill="x", padx=18, pady=(16, 8))

                # Kayıt numarası
                ctk.CTkLabel(
                    top_row,
                    text=f"Record #{repair_id}",
                    font=("Arial", 12, "bold"),
                    text_color="white",
                    fg_color=self.primary_color,
                    corner_radius=12,
                    padx=12,
                    pady=4
                ).pack(side="left")

                # Feedback puanı
                ctk.CTkLabel(
                    top_row,
                    text=f"{feedback.rating}/5",
                    font=("Arial", 14, "bold"),
                    text_color=self.primary_color
                ).pack(side="right")

                # Feedback bilgi alanı
                info_frame = ctk.CTkFrame(feedback_card, fg_color="transparent")
                info_frame.pack(fill="x", padx=18, pady=(4, 16))

                # Müşteri adı
                ctk.CTkLabel(
                    info_frame,
                    text=f"Customer: {feedback.customer}",
                    font=("Arial", 15, "bold"),
                    anchor="w"
                ).pack(anchor="w", pady=(0, 6))

                # Feedback yorumu
                ctk.CTkLabel(
                    info_frame,
                    text=feedback.comment,
                    font=("Arial", 13),
                    text_color=self.get_sub_text_color(),
                    wraplength=560,
                    justify="left",
                    anchor="w"
                ).pack(anchor="w", pady=(2, 4))

        # Pencere kapatma butonu
        ctk.CTkButton(
            main_card,
            text="Close",
            width=160,
            height=38,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=win.destroy
        ).pack(pady=(0, 20))