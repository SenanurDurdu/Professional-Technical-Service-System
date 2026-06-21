import customtkinter as ctk
from tkinter import simpledialog

from models import Warranty, SparePart, PartUsage, ServiceCenter


# Garanti, stok, yedek parça, servis merkezi ve cihaz geçmişi işlemlerini yöneten sınıf.
class ServiceActions:

    # Seçilen cihaz için garanti bilgisi ekler veya mevcut garantiyi günceller.
    def manage_warranty(self):

        # Tablodan seçilen kaydı alır
        item = self.get_selected_item()

        if not item:
            return

        # Seçilen kayıttan seri numarası ve cihaz modeli alınır
        serial_no = item[4]
        device_model = item[3]

        # Bu seri numarasına ait garanti kaydı var mı kontrol edilir
        warranty = self.db.get_warranty(serial_no)

        current_expiry_date = ""

        # Eğer garanti varsa mevcut bitiş tarihi alınır
        if warranty:
            _, current_expiry_date = warranty

        # Garanti penceresi oluşturulur
        win = ctk.CTkToplevel(self)
        win.title("Warranty Information")
        win.geometry("500x470")
        win.resizable(False, False)
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)
        win.grab_set()

        # Ana kart alanı
        card = ctk.CTkFrame(win, corner_radius=22)
        card.pack(fill="both", expand=True, padx=24, pady=24)

        # Garanti varsa farklı, yoksa farklı başlık gösterilir
        title_text = "WARRANTY STATUS" if warranty else "ADD WARRANTY"

        ctk.CTkLabel(
            card,
            text=title_text,
            font=("Arial", 23, "bold"),
            text_color=self.primary_color
        ).pack(pady=(25, 6))

        # Kullanıcıya bilgilendirme metni gösterilir
        info_text = (
            "This device already has a warranty record."
            if warranty
            else "Create a warranty record for this device."
        )

        ctk.CTkLabel(
            card,
            text=info_text,
            font=("Arial", 13),
            text_color=self.get_sub_text_color()
        ).pack(pady=(0, 18))

        # Cihaz bilgilerinin gösterileceği alan
        info_frame = ctk.CTkFrame(card, corner_radius=16)
        info_frame.pack(fill="x", padx=24, pady=8)

        # Gösterilecek temel bilgiler
        rows = [
            ("Device", device_model),
            ("Serial No / IMEI", serial_no)
        ]

        # Mevcut garanti varsa listeye eklenir
        if warranty:
            rows.append(("Current Warranty", current_expiry_date))

        # Bilgiler ekrana satır satır yazdırılır
        for label, value in rows:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=8)

            ctk.CTkLabel(
                row,
                text=label + ":",
                font=("Arial", 13, "bold"),
                width=140,
                anchor="w"
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=str(value),
                font=("Arial", 13),
                anchor="w"
            ).pack(side="left")

        # Garanti bitiş tarihi giriş alanı
        date_entry = ctk.CTkEntry(
            card,
            placeholder_text="Warranty Expiry Date (Example: 20/06/2027)",
            width=330,
            height=38
        )
        date_entry.pack(pady=(22, 8))

        # Mevcut garanti varsa tarih alanına yazılır
        if warranty:
            date_entry.insert(0, current_expiry_date)

        # Tarih formatı bilgisi
        ctk.CTkLabel(
            card,
            text="Date format must be DD/MM/YYYY.",
            font=("Arial", 12),
            text_color=self.get_sub_text_color()
        ).pack(pady=(0, 12))

        # Buton alanı
        button_frame = ctk.CTkFrame(card, fg_color="transparent")
        button_frame.pack(pady=(10, 20))

        # Garanti bilgisini kaydeden iç fonksiyon
        def save_warranty():

            # Kullanıcının girdiği garanti bitiş tarihi alınır
            expiry_date = date_entry.get().strip()

            # Tarih boş bırakılamaz
            if not expiry_date:
                return self.show_msg(
                    "Error",
                    "Warranty expiry date cannot be empty.",
                    "warning",
                    win
                )

            # Tarihin geçmiş tarih olup olmadığı kontrol edilir
            past_result = self.is_past_date(expiry_date)

            # Tarih formatı hatalıysa uyarı verir
            if past_result is None:
                return self.show_msg(
                    "Error",
                    "Date format must be DD/MM/YYYY.",
                    "warning",
                    win
                )

            # Garanti tarihi geçmiş tarih olamaz
            if past_result:
                return self.show_msg(
                    "Error",
                    "Warranty expiry date cannot be a past date.",
                    "warning",
                    win
                )

            # Warranty nesnesi oluşturulur
            warranty_obj = Warranty(serial_no, expiry_date)

            # Garanti bilgisi veritabanına kaydedilir veya güncellenir
            self.db.add_warranty(warranty_obj)

            # Başarı mesajı gösterilir
            self.show_msg(
                "Success",
                "Warranty information saved.",
                "info",
                win
            )

            # Pencere kapatılır
            win.destroy()

        # Garanti varsa buton update, yoksa save olarak gösterilir
        button_text = "Update Warranty" if warranty else "Save Warranty"

        # Garanti kaydetme / güncelleme butonu
        ctk.CTkButton(
            button_frame,
            text=button_text,
            width=150,
            height=36,
            fg_color=self.primary_color,
            command=save_warranty
        ).pack(side="left", padx=8)

        # İptal butonu
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=120,
            height=36,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=win.destroy
        ).pack(side="left", padx=8)

    # Yedek parça stoklarını yönetir.
    def manage_spare_parts(self):

        # Stok yönetimi penceresi oluşturulur
        win = ctk.CTkToplevel(self)
        win.title("Stock Management")
        win.geometry("520x520")
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        # Ana kart alanı
        card = ctk.CTkFrame(win, corner_radius=16)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        # Başlık
        ctk.CTkLabel(
            card,
            text="Stock Management",
            font=("Arial", 20, "bold")
        ).pack(pady=15)

        # Parça adı giriş alanı
        name_entry = ctk.CTkEntry(card, placeholder_text="Part Name", width=280)
        name_entry.pack(pady=6)

        # Parça fiyatı giriş alanı
        price_entry = ctk.CTkEntry(card, placeholder_text="Price", width=280)
        price_entry.pack(pady=6)

        # Stok miktarı giriş alanı
        stock_entry = ctk.CTkEntry(card, placeholder_text="Stock", width=280)
        stock_entry.pack(pady=6)

        # Mevcut parçaların gösterileceği metin kutusu
        text_box = ctk.CTkTextbox(card, width=440, height=230)
        text_box.pack(padx=20, pady=15)

        # Parça listesini ekranda yeniler
        def refresh_parts():

            # Textbox düzenlenebilir hale getirilir
            text_box.configure(state="normal")

            # Eski içerik temizlenir
            text_box.delete("0.0", "end")

            # Başlık yazılır
            text_box.insert("end", "SPARE PARTS\n" + "=" * 35 + "\n")

            # Veritabanındaki tüm parçalar listelenir
            for name, price, stock in self.db.get_spare_parts():
                part = SparePart(name, price, stock)
                text_box.insert(
                    "end",
                    f"{part.name} | {part.price} TL | Stock: {part.stock}\n"
                )

            # Textbox tekrar sadece okunabilir yapılır
            text_box.configure(state="disabled")

        # Yeni parça ekler veya mevcut parçayı günceller
        def add_part():

            # Parça adı alınır
            name = name_entry.get().strip()

            # Fiyat ve stok sayısal olmalıdır
            try:
                price = float(price_entry.get())
                stock = int(stock_entry.get())
            except ValueError:
                return self.show_msg(
                    "Error",
                    "Price and stock must be numeric.",
                    "warning",
                    win
                )

            # Parça adı boş olamaz
            if not name:
                return self.show_msg("Error", "Part name cannot be empty.", "warning", win)

            # Parça fiyatı sıfır veya negatif olamaz
            if price <= 0:
                return self.show_msg("Error", "Part price cannot be zero or negative.", "warning", win)

            # Stok negatif olamaz
            if stock < 0:
                return self.show_msg("Error", "Stock cannot be negative.", "warning", win)

            # SparePart nesnesi oluşturulur
            part = SparePart(name, price, stock)

            # Parça veritabanına eklenir veya güncellenir
            self.db.add_spare_part(part)

            # Liste yenilenir
            refresh_parts()

        # Parça ekleme / güncelleme butonu
        ctk.CTkButton(
            card,
            text="Add / Update Part",
            width=280,
            fg_color=self.primary_color,
            command=add_part
        ).pack(pady=8)

        # Pencere açıldığında mevcut parçalar listelenir
        refresh_parts()

    # Seçilen tamir kaydı için yedek parça kullanımı yapar.
    def use_spare_part(self):

        # Tablodan seçilen kayıt alınır
        item = self.get_selected_item()

        if not item:
            return

        # Kayıt ID ve durum bilgisi alınır
        repair_id = item[0]
        status = item[6]

        # Reddedilen kayıtta parça kullanılamaz
        if status == "Rejected":
            return self.show_msg(
                "Error",
                "Spare parts cannot be used because this repair request was rejected.",
                "warning"
            )

        # Tamamlanmış kayıtta parça kullanılamaz
        if status == "Completed":
            return self.show_msg(
                "Error",
                "Spare parts cannot be used because this repair has already been completed.",
                "warning"
            )

        # Parça sadece Repairing aşamasında kullanılabilir
        if status != "Repairing":
            return self.show_msg(
                "Error",
                "Spare parts can only be used during the Repairing stage.",
                "warning"
            )

        # Veritabanından tüm parçalar alınır
        parts = self.db.get_spare_parts()

        # Hiç parça yoksa hata verir
        if not parts:
            return self.show_msg("Error", "There are no spare parts in stock.", "warning")

        # Stokta olan parçalar filtrelenir
        available_parts = [part[0] for part in parts if part[2] > 0]

        # Stokta kullanılabilir parça yoksa hata verir
        if not available_parts:
            return self.show_msg("Error", "There are no available spare parts in stock.", "warning")

        # Parça kullanımı penceresi oluşturulur
        win = ctk.CTkToplevel(self)
        win.title("Use Spare Part")
        win.geometry("360x260")
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        # Kullanılacak parça seçimi
        combo = ctk.CTkComboBox(win, values=available_parts, width=240)
        combo.pack(pady=25)
        combo.set(available_parts[0])

        # Miktar giriş alanı
        qty_entry = ctk.CTkEntry(win, placeholder_text="Quantity", width=240)
        qty_entry.pack(pady=8)

        # Parça kullanımını kaydeden iç fonksiyon
        def save_usage():

            # Miktar sayısal olmalıdır
            try:
                quantity = int(qty_entry.get())
            except ValueError:
                return self.show_msg("Error", "Quantity must be numeric.", "warning", win)

            # Miktar sıfır veya negatif olamaz
            if quantity <= 0:
                return self.show_msg("Error", "Quantity must be greater than 0.", "warning", win)

            # PartUsage nesnesi oluşturulur
            part_usage = PartUsage(repair_id, combo.get(), quantity)

            # Parça kullanımı veritabanına kaydedilir
            success, msg = self.db.use_part(part_usage)

            # İşlem başarılıysa log kaydı oluşturulur
            if success:
                self.logger.log_action(
                    f"{quantity} units of {combo.get()} were used for record {repair_id}."
                )

                self.show_msg("Success", msg, "info", win)
                win.destroy()
                self.show_home_page()

            # İşlem başarısızsa hata mesajı gösterilir
            else:
                self.show_msg("Error", msg, "warning", win)

        # Kaydet butonu
        ctk.CTkButton(
            win,
            text="Save",
            fg_color=self.primary_color,
            command=save_usage
        ).pack(pady=12)

    # Yeni servis merkezi ekler veya mevcut merkezi günceller.
    def manage_service_center(self):

        # Servis merkezi penceresi oluşturulur
        win = ctk.CTkToplevel(self)
        win.title("Add Service Center")
        win.geometry("500x430")
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
            text="ADD SERVICE CENTER",
            font=("Arial", 24, "bold"),
            text_color=self.primary_color
        ).pack(pady=(28, 6))

        # Açıklama
        ctk.CTkLabel(
            main_card,
            text="Register a technical service branch with its location.",
            font=("Arial", 13),
            text_color=self.get_sub_text_color()
        ).pack(pady=(0, 22))

        # Form alanı
        form_frame = ctk.CTkFrame(main_card, corner_radius=18)
        form_frame.pack(fill="x", padx=28, pady=10)

        # Servis merkezi adı etiketi
        ctk.CTkLabel(
            form_frame,
            text="Service Center Name",
            font=("Arial", 13, "bold"),
            anchor="w"
        ).pack(fill="x", padx=22, pady=(18, 4))

        # Servis merkezi adı giriş alanı
        name_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Example: Central Technical Service",
            height=38
        )
        name_entry.pack(fill="x", padx=22, pady=(0, 12))

        # Konum etiketi
        ctk.CTkLabel(
            form_frame,
            text="Location",
            font=("Arial", 13, "bold"),
            anchor="w"
        ).pack(fill="x", padx=22, pady=(4, 4))

        # Konum giriş alanı
        location_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Example: Istanbul / Kartal",
            height=38
        )
        location_entry.pack(fill="x", padx=22, pady=(0, 20))

        # Buton alanı
        button_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        button_frame.pack(pady=(16, 22))

        # Servis merkezini kaydeden iç fonksiyon
        def save_center():

            # Girilen bilgiler alınır
            name = name_entry.get().strip()
            location = location_entry.get().strip()

            # Servis merkezi adı boş olamaz
            if not name:
                return self.show_msg(
                    "Error",
                    "Service center name cannot be empty.",
                    "warning",
                    win
                )

            # Konum boş olamaz
            if not location:
                return self.show_msg(
                    "Error",
                    "Service center location cannot be empty.",
                    "warning",
                    win
                )

            # ServiceCenter nesnesi oluşturulur
            service_center = ServiceCenter(name, location)

            # Servis merkezi veritabanına kaydedilir
            self.db.add_service_center(service_center)

            # Başarı mesajı gösterilir
            self.show_msg(
                "Success",
                "Service center saved.",
                "info",
                win
            )

            # Pencere kapatılır
            win.destroy()

        # Kaydet butonu
        ctk.CTkButton(
            button_frame,
            text="Save Center",
            width=150,
            height=38,
            fg_color=self.primary_color,
            command=save_center
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

    # Sistemdeki servis merkezlerini listeler.
    def show_service_centers(self):

        # Servis merkezleri veritabanından alınır
        rows = self.db.get_service_centers()

        # Servis merkezleri penceresi oluşturulur
        win = ctk.CTkToplevel(self)
        win.title("Service Centers")
        win.geometry("620x560")
        win.resizable(False, False)
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        # Ana kart
        main_card = ctk.CTkFrame(win, corner_radius=24)
        main_card.pack(fill="both", expand=True, padx=24, pady=24)

        # Başlık alanı
        header_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(24, 8))

        # Sol başlık alanı
        left_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_header.pack(side="left", anchor="w")

        # Sayfa başlığı
        ctk.CTkLabel(
            left_header,
            text="SERVICE CENTERS",
            font=("Arial", 24, "bold"),
            text_color=self.primary_color
        ).pack(anchor="w")

        # Açıklama yazısı
        ctk.CTkLabel(
            left_header,
            text="Registered technical service branches",
            font=("Arial", 13),
            text_color=self.get_sub_text_color()
        ).pack(anchor="w", pady=(4, 0))

        # Servis merkezi sayısını gösteren etiket
        count_badge = ctk.CTkLabel(
            header_frame,
            text=f"{len(rows)} Center(s)",
            font=("Arial", 12, "bold"),
            text_color="white",
            fg_color=self.primary_color,
            corner_radius=14,
            padx=14,
            pady=6
        )
        count_badge.pack(side="right", anchor="ne")

        # Scrollable liste alanı
        scroll = ctk.CTkScrollableFrame(main_card, corner_radius=18)
        scroll.pack(fill="both", expand=True, padx=24, pady=16)

        # Servis merkezi yoksa bilgi kartı gösterilir
        if not rows:
            empty_card = ctk.CTkFrame(scroll, corner_radius=18)
            empty_card.pack(fill="x", padx=12, pady=35)

            ctk.CTkLabel(
                empty_card,
                text="No Service Center Found",
                font=("Arial", 18, "bold"),
                text_color=self.primary_color
            ).pack(pady=(28, 6))

            ctk.CTkLabel(
                empty_card,
                text="You can add a new service center from the management menu.",
                font=("Arial", 13),
                text_color=self.get_sub_text_color()
            ).pack(pady=(0, 28))

        else:

            # Her servis merkezi için kart oluşturulur
            for index, row in enumerate(rows, 1):
                name, location = row
                center = ServiceCenter(name, location)

                center_card = ctk.CTkFrame(scroll, corner_radius=18)
                center_card.pack(fill="x", padx=12, pady=10)

                # Kart üst satırı
                top_row = ctk.CTkFrame(center_card, fg_color="transparent")
                top_row.pack(fill="x", padx=18, pady=(16, 8))

                # Servis merkezi sıra bilgisi
                ctk.CTkLabel(
                    top_row,
                    text=f"Center #{index}",
                    font=("Arial", 12, "bold"),
                    text_color="white",
                    fg_color=self.primary_color,
                    corner_radius=12,
                    padx=12,
                    pady=4
                ).pack(side="left")

                # Aktif etiketi
                ctk.CTkLabel(
                    top_row,
                    text="Active",
                    font=("Arial", 12, "bold"),
                    text_color="#2ecc71"
                ).pack(side="right")

                # Merkez bilgi alanı
                info_frame = ctk.CTkFrame(center_card, fg_color="transparent")
                info_frame.pack(fill="x", padx=18, pady=(4, 16))

                # Servis merkezi adı
                ctk.CTkLabel(
                    info_frame,
                    text=center.name,
                    font=("Arial", 18, "bold"),
                    anchor="w"
                ).pack(anchor="w", pady=(0, 6))

                # Servis merkezi konumu
                ctk.CTkLabel(
                    info_frame,
                    text=f"Location: {center.location}",
                    font=("Arial", 13),
                    text_color=self.get_sub_text_color(),
                    anchor="w"
                ).pack(anchor="w")

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

    # Seçilen cihazın geçmiş tamir kayıtlarını gösterir.
    def show_history(self):

        # Tablodan seçilen kayıt alınır
        item = self.get_selected_item()

        if not item:
            return

        # Seçilen cihazın seri numarası alınır
        serial_no = item[4]

        # Seri numarasına göre cihaz geçmişi veritabanından çekilir
        rows = self.db.get_device_history(serial_no)

        # Cihaz geçmişi penceresi oluşturulur
        win = ctk.CTkToplevel(self)
        win.title(f"Device History - {serial_no}")
        win.geometry("680x620")
        win.resizable(False, False)
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        # Ana kart
        main_card = ctk.CTkFrame(win, corner_radius=22)
        main_card.pack(fill="both", expand=True, padx=24, pady=24)

        # Başlık
        ctk.CTkLabel(
            main_card,
            text="DEVICE HISTORY",
            font=("Arial", 24, "bold"),
            text_color=self.primary_color
        ).pack(pady=(22, 4))

        # Seri numarası bilgisi
        ctk.CTkLabel(
            main_card,
            text=f"Serial No / IMEI: {serial_no}",
            font=("Arial", 13),
            text_color=self.get_sub_text_color()
        ).pack(pady=(0, 18))

        # Scrollable geçmiş alanı
        scroll = ctk.CTkScrollableFrame(main_card, corner_radius=16)
        scroll.pack(fill="both", expand=True, padx=22, pady=10)

        # Cihaza ait geçmiş yoksa bilgi verir
        if not rows:
            ctk.CTkLabel(
                scroll,
                text="No history was found for this device.",
                font=("Arial", 14),
                text_color=self.get_sub_text_color()
            ).pack(pady=40)

        else:

            # Her geçmiş kaydı için kart oluşturulur
            for row in rows:
                row_repair_id = row[0]
                process_date = row[1]
                damage_desc = row[2]
                status = row[3]
                price = row[4]
                delivery_date = row[5]

                record_card = ctk.CTkFrame(scroll, corner_radius=16)
                record_card.pack(fill="x", padx=10, pady=10)

                # Kart üst satırı
                top_row = ctk.CTkFrame(record_card, fg_color="transparent")
                top_row.pack(fill="x", padx=18, pady=(14, 6))

                # Kayıt numarası
                ctk.CTkLabel(
                    top_row,
                    text=f"Record #{row_repair_id}",
                    font=("Arial", 16, "bold")
                ).pack(side="left")

                # Kayıt durumu
                ctk.CTkLabel(
                    top_row,
                    text=status,
                    font=("Arial", 12, "bold"),
                    text_color="white",
                    fg_color=self.primary_color,
                    corner_radius=10,
                    padx=12,
                    pady=4
                ).pack(side="right")

                # Geçmişte gösterilecek bilgiler
                info_rows = [
                    ("Process Date", process_date),
                    ("Damage", damage_desc),
                    ("Cost", f"{price} TL"),
                    ("Delivery Date", delivery_date)
                ]

                # Bilgiler satır satır eklenir
                for label, value in info_rows:
                    info_row = ctk.CTkFrame(record_card, fg_color="transparent")
                    info_row.pack(fill="x", padx=18, pady=4)

                    ctk.CTkLabel(
                        info_row,
                        text=label + ":",
                        font=("Arial", 13, "bold"),
                        width=120,
                        anchor="w"
                    ).pack(side="left")

                    ctk.CTkLabel(
                        info_row,
                        text=str(value),
                        font=("Arial", 13),
                        anchor="w"
                    ).pack(side="left")

                # Bu kayıtta kullanılan parçalar alınır
                part_usages = self.db.get_part_usages(row_repair_id)

                # Kullanılan parça varsa ayrı alanda gösterilir
                if part_usages:
                    parts_frame = ctk.CTkFrame(record_card, corner_radius=12)
                    parts_frame.pack(fill="x", padx=18, pady=(10, 14))

                    ctk.CTkLabel(
                        parts_frame,
                        text="Used Spare Parts",
                        font=("Arial", 13, "bold"),
                        text_color=self.primary_color
                    ).pack(anchor="w", padx=14, pady=(10, 4))

                    # Kullanılan parçalar listelenir
                    for part_name, quantity in part_usages:
                        ctk.CTkLabel(
                            parts_frame,
                            text=f"• {part_name}  |  Quantity: {quantity}",
                            font=("Arial", 12),
                            anchor="w"
                        ).pack(anchor="w", padx=18, pady=2)

        # Pencere kapatma butonu
        ctk.CTkButton(
            main_card,
            text="Close",
            width=180,
            height=36,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=win.destroy
        ).pack(pady=(8, 18))