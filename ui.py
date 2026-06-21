import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
from PIL import Image

from database import DatabaseManager
from models import Customer, Technician, Master, UserAccount, NotificationDetail
from helpers import (
    SecurityManager,
    LoggerSystem,
    NotificationSystem,
    SystemSettings,
    StatisticsManager
)
from actions import AppActionsMixin


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class TechApp(AppActionsMixin, ctk.CTk):
    def __init__(self):
        super().__init__()

        self.db = DatabaseManager()
        self.logger = LoggerSystem()
        self.notification_system = NotificationSystem()

        self.settings = SystemSettings()
        db_settings = self.db.get_settings()

        if db_settings:
            self.settings = SystemSettings(db_settings[0], db_settings[1])
            ctk.set_appearance_mode(self.settings.theme)
            ctk.set_default_color_theme(self.get_ctk_theme_name(self.settings.theme_color))

        self.primary_color = self.get_primary_color()

        self.current_user = None
        self.user_role = None
        self.current_person = None
        self.active_menu = "Home"

        self.title("Professional Technical Service System")
        self.geometry("1280x760")
        self.minsize(1100, 700)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.main_layout = None
        self.sidebar = None
        self.content = None
        self.tree = None
        self.login_bg_image = None
        self.register_bg_image = None

        self.show_login()

    def get_ctk_theme_name(self, theme_color):
        if theme_color == "Green":
            return "green"

        if theme_color == "Dark Blue":
            return "dark-blue"

        return "blue"

    def get_primary_color(self):
        colors = {
            "Blue": "#1f6aa5",
            "Green": "#2fa572",
            "Dark Blue": "#144870",
            "Purple": "#7B2CBF",
            "Orange": "#F77F00",
            "Red": "#D62828",
            "Teal": "#008080",
            "Pink": "#C2185B"
        }

        return colors.get(self.settings.theme_color, "#1f6aa5")

    def get_text_color(self):
        if self.settings.theme == "Light":
            return "#222222"
        return "#ffffff"

    def get_sub_text_color(self):
        if self.settings.theme == "Light":
            return "#555555"
        return "#b0b0b0"

    def get_hover_color(self):
        if self.settings.theme == "Light":
            return "#d9e8f5"
        return "#2f3a45"

    def get_secondary_button_color(self):
        if self.settings.theme == "Light":
            return "#e0e0e0"
        return "#3a3a3a"

    def on_closing(self):
        self.db.close_connection()
        self.destroy()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def clear_content(self):
        if self.content is None:
            return

        for widget in self.content.winfo_children():
            widget.destroy()

        self.tree = None

    def show_msg(self, title, text, msg_type="info", parent=None):
        parent = parent or self

        if msg_type == "info":
            return messagebox.showinfo(title, text, parent=parent)

        if msg_type == "warning":
            return messagebox.showwarning(title, text, parent=parent)

        return messagebox.showerror(title, text, parent=parent)

    def ask_yes_no(self, title, text, parent=None):
        result = {"answer": False}

        win = ctk.CTkToplevel(parent or self)
        win.title(title)
        win.geometry("360x190")
        win.resizable(False, False)
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)
        win.grab_set()

        ctk.CTkLabel(win, text=title, font=("Arial", 18, "bold")).pack(pady=(22, 8))

        ctk.CTkLabel(
            win,
            text=text,
            wraplength=310,
            font=("Arial", 13)
        ).pack(pady=8)

        button_frame = ctk.CTkFrame(win, fg_color="transparent")
        button_frame.pack(pady=18)

        def yes_action():
            result["answer"] = True
            win.destroy()

        def no_action():
            result["answer"] = False
            win.destroy()

        ctk.CTkButton(
            button_frame,
            text="Yes",
            width=100,
            fg_color=self.primary_color,
            command=yes_action
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            button_frame,
            text="No",
            width=100,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=no_action
        ).pack(side="left", padx=8)

        self.wait_window(win)
        return result["answer"]

    def create_person_object(self, username, role, email=""):
        if role == "Customer":
            return Customer(username, email)

        if role == "Technician":
            return Technician(username)

        return Master(username)

    def get_selected_item(self):
        if not hasattr(self, "tree") or self.tree is None:
            self.show_msg(
                "Error",
                "You must go to the Home page and select a record first.",
                "warning"
            )
            return None

        try:
            if not self.tree.winfo_exists():
                self.tree = None
                self.show_msg(
                    "Error",
                    "You must go to the Home page and select a record first.",
                    "warning"
                )
                return None

            selected = self.tree.selection()

        except Exception:
            self.tree = None
            self.show_msg(
                "Error",
                "You must go to the Home page and select a record first.",
                "warning"
            )
            return None

        if not selected:
            self.show_msg(
                "Error",
                "Please select a record from the table first.",
                "warning"
            )
            return None

        return self.tree.item(selected[0])["values"]

    def open_text_window(self, title, content):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("620x500")
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)

        text_box = ctk.CTkTextbox(win, width=560, height=430)
        text_box.pack(padx=25, pady=25)
        text_box.insert("0.0", content)
        text_box.configure(state="disabled")

    def is_past_date(self, date_text):
        try:
            selected_date = datetime.strptime(date_text, "%d/%m/%Y").date()
            today = datetime.now().date()
            return selected_date < today
        except ValueError:
            return None

    def add_notification_for_user(self, username, title, message):
        notification = NotificationDetail(title, message, username)
        self.notification_system.add_notification(notification.message)
        self.db.add_notification(notification)

    def show_login(self):
        self.clear_window()
        self.geometry("1280x760")

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True)

        try:
            self.login_bg_image = ctk.CTkImage(
                light_image=Image.open("pictures/login_bg.jpg"),
                dark_image=Image.open("pictures/login_bg.jpg"),
                size=(1280, 760)
            )

            bg_label = ctk.CTkLabel(
                wrapper,
                image=self.login_bg_image,
                text=""
            )
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        except Exception:
            wrapper.configure(fg_color="#111111")

        login_card = ctk.CTkFrame(
            wrapper,
            width=430,
            height=470,
            corner_radius=26,
            fg_color=("#f2f2f2", "#111111")
        )
        login_card.place(relx=0.5, rely=0.5, anchor="center")
        login_card.pack_propagate(False)

        ctk.CTkLabel(
            login_card,
            text="Technical Service System",
            font=("Arial", 28, "bold")
        ).pack(pady=(35, 8))

        ctk.CTkLabel(
            login_card,
            text="Manage device tracking and service operations",
            font=("Arial", 14),
            text_color=self.get_sub_text_color()
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            login_card,
            text="Log in to your account",
            font=("Arial", 13),
            text_color=self.get_sub_text_color()
        ).pack(pady=(0, 24))

        self.e_u = ctk.CTkEntry(login_card, placeholder_text="Username", width=300, height=40)
        self.e_u.pack(pady=8)

        self.e_p = ctk.CTkEntry(login_card, placeholder_text="Password", width=300, height=40, show="*")
        self.e_p.pack(pady=8)

        self.r_v = ctk.CTkComboBox(
            login_card,
            values=["Master", "Technician", "Customer"],
            width=300,
            height=40,
            state="readonly"
        )
        self.r_v.pack(pady=8)
        self.r_v.set("Customer")

        ctk.CTkButton(
            login_card,
            text="Log In",
            width=300,
            height=40,
            fg_color=self.primary_color,
            command=self.login_act
        ).pack(pady=(22, 8))

        ctk.CTkButton(
            login_card,
            text="Create New Account",
            width=300,
            height=40,
            fg_color=("#dcdcdc", "#2b2b2b"),
            hover_color=self.get_hover_color(),
            text_color=self.get_text_color(),
            command=self.open_register
        ).pack(pady=8)

    def open_register(self):
        self.withdraw()

        self.reg_win = ctk.CTkToplevel(self)
        self.reg_win.geometry("760x560")
        self.reg_win.title("Register")
        self.reg_win.lift()
        self.reg_win.focus_force()
        self.reg_win.attributes("-topmost", True)

        wrapper = ctk.CTkFrame(self.reg_win, fg_color="transparent")
        wrapper.pack(fill="both", expand=True)

        try:
            self.register_bg_image = ctk.CTkImage(
                light_image=Image.open("pictures/login_bg.jpg"),
                dark_image=Image.open("pictures/login_bg.jpg"),
                size=(760, 560)
            )

            bg_label = ctk.CTkLabel(
                wrapper,
                image=self.register_bg_image,
                text=""
            )
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        except Exception:
            wrapper.configure(fg_color="#111111")

        card = ctk.CTkFrame(
            wrapper,
            width=430,
            height=490,
            corner_radius=20,
            fg_color=("#e6e6e6", "#1f1f1f")
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        ctk.CTkLabel(card, text="New Registration", font=("Arial", 24, "bold")).pack(pady=(25, 20))

        self.reg_u = ctk.CTkEntry(card, placeholder_text="Username", width=310, height=38)
        self.reg_u.pack(pady=8)

        self.reg_e = ctk.CTkEntry(card, placeholder_text="Email (@gmail.com)", width=310, height=38)
        self.reg_e.pack(pady=8)

        self.reg_p1 = ctk.CTkEntry(card, placeholder_text="Password (Min 6 characters)", width=310, height=38, show="*")
        self.reg_p1.pack(pady=8)

        self.reg_p2 = ctk.CTkEntry(card, placeholder_text="Confirm Password", width=310, height=38, show="*")
        self.reg_p2.pack(pady=8)

        self.reg_r = ctk.CTkComboBox(
            card,
            values=["Master", "Technician", "Customer"],
            width=310,
            height=38,
            state="readonly"
        )
        self.reg_r.pack(pady=8)
        self.reg_r.set("Customer")

        ctk.CTkButton(
            card,
            text="Register",
            width=310,
            height=38,
            fg_color=self.primary_color,
            command=self.do_register
        ).pack(pady=(22, 8))

        ctk.CTkButton(
            card,
            text="Back",
            width=310,
            height=38,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.back_to_login
        ).pack(pady=8)

    def back_to_login(self):
        self.reg_win.destroy()
        self.deiconify()

    def do_register(self):
        username = self.reg_u.get().strip()
        email = self.reg_e.get().strip()
        password1 = self.reg_p1.get()
        password2 = self.reg_p2.get()
        role = self.reg_r.get()

        if not all([username, email, password1, password2]):
            return self.show_msg("Error", "Please fill in all fields.", "warning", self.reg_win)

        if not email.endswith("@gmail.com"):
            return self.show_msg("Error", "Please enter a valid Gmail address.", "warning", self.reg_win)

        if not SecurityManager.check_password_length(password1):
            return self.show_msg("Error", "Password must be at least 6 characters long.", "warning", self.reg_win)

        if password1 != password2:
            return self.show_msg("Error", "Passwords do not match.", "warning", self.reg_win)

        user_account = UserAccount(username, SecurityManager.hash_password(password1), role, email)
        success, msg = self.db.register_user(user_account)

        if success:
            person = self.create_person_object(username, role, email)
            self.logger.log_action(f"New user registered: {person.username} ({role})")
            self.show_msg("Success", "Registration completed successfully.", "info", self.reg_win)
            self.reg_win.destroy()
            self.deiconify()
        else:
            self.show_msg("Error", msg, "error", self.reg_win)

    def login_act(self):
        username = self.e_u.get().strip()
        password = self.e_p.get()
        role = self.r_v.get()

        if not username:
            return self.show_msg("Error", "Username cannot be empty.", "warning")

        if not password:
            return self.show_msg("Error", "Password cannot be empty.", "warning")

        success, msg, email = self.db.check_login(username, SecurityManager.hash_password(password), role)

        if not success:
            return self.show_msg("Login Error", msg, "error")

        self.current_user = username
        self.user_role = role
        self.current_person = self.create_person_object(username, role, email)

        self.logger.log_action(f"{self.current_person.username} logged in. Role: {role}")
        self.geometry("1280x760")
        self.show_dashboard()

    def show_dashboard(self):
        self.clear_window()

        self.main_layout = ctk.CTkFrame(self, fg_color="transparent")
        self.main_layout.pack(fill="both", expand=True, padx=14, pady=14)

        self.sidebar = ctk.CTkFrame(self.main_layout, width=230, corner_radius=18)
        self.sidebar.pack(side="left", fill="y", padx=(0, 14))
        self.sidebar.pack_propagate(False)

        self.content = ctk.CTkFrame(self.main_layout, corner_radius=18)
        self.content.pack(side="right", fill="both", expand=True)

        self.create_sidebar()
        self.show_home_page()

    def set_active_menu(self, menu_name):
        self.active_menu = menu_name
        self.create_sidebar()

    def run_menu_action(self, menu_name, command):
        self.set_active_menu(menu_name)
        command()

    def create_sidebar(self):
        for widget in self.sidebar.winfo_children():
            widget.destroy()

        header_card = ctk.CTkFrame(self.sidebar, corner_radius=18)
        header_card.pack(fill="x", padx=12, pady=(16, 10))

        ctk.CTkLabel(
            header_card,
            text="Technical Service",
            font=("Arial", 19, "bold")
        ).pack(pady=(16, 4))

        ctk.CTkLabel(
            header_card,
            text=f"{self.user_role} Panel",
            font=("Arial", 12, "bold"),
            text_color="white",
            fg_color=self.primary_color,
            corner_radius=14,
            padx=12,
            pady=4
        ).pack(pady=(2, 6))

        ctk.CTkLabel(
            header_card,
            text=f"@{self.current_user}",
            font=("Arial", 12),
            text_color=self.get_sub_text_color()
        ).pack(pady=(0, 14))

        scroll_menu = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        scroll_menu.pack(fill="both", expand=True, padx=10, pady=4)

        def create_group(title):
            group = ctk.CTkFrame(scroll_menu, corner_radius=16)
            group.pack(fill="x", pady=7)

            ctk.CTkLabel(
                group,
                text=title,
                font=("Arial", 11, "bold"),
                text_color=self.primary_color
            ).pack(anchor="w", padx=12, pady=(10, 4))

            return group

        def add_button(parent, text, command):
            is_active = text == self.active_menu

            ctk.CTkButton(
                parent,
                text=text,
                height=34,
                corner_radius=10,
                anchor="w",
                fg_color=self.primary_color if is_active else "transparent",
                hover_color=self.get_hover_color(),
                text_color="white" if is_active else self.get_text_color(),
                command=lambda t=text, c=command: self.run_menu_action(t, c)
            ).pack(fill="x", padx=8, pady=3)

        main_group = create_group("MAIN")
        add_button(main_group, "Home", self.show_home_page)

        if self.user_role == "Customer":
            repair_group = create_group("REPAIR")
            add_button(repair_group, "New Repair Request", self.show_new_repair_page)
            add_button(repair_group, "Change Technician", self.change_technician)

            offer_group = create_group("OFFER")
            add_button(offer_group, "Approve Repair Offer", lambda: self.change_status("Repairing"))
            add_button(offer_group, "Reject Repair Offer", lambda: self.change_status("Rejected"))

            payment_group = create_group("PAYMENT")
            add_button(payment_group, "Make Payment", self.pay_repair)
            add_button(payment_group, "View Invoice", self.show_invoice)

            service_group = create_group("SERVICE")
            add_button(service_group, "Give Feedback", self.give_feedback)
            add_button(service_group, "Create Appointment", self.create_appointment)
            add_button(service_group, "Warranty", self.manage_warranty)

            communication_group = create_group("COMMUNICATION")
            add_button(communication_group, "Send Message", self.send_message)

        elif self.user_role == "Technician":
            repair_group = create_group("REPAIR PROCESS")
            add_button(repair_group, "Start Diagnosis", lambda: self.change_status("Diagnosing"))
            add_button(repair_group, "Complete Repair", lambda: self.change_status("Completed"))

            stock_group = create_group("PARTS")
            add_button(stock_group, "Use Spare Part", self.use_spare_part)

            communication_group = create_group("COMMUNICATION")
            add_button(communication_group, "Send Message", self.send_message)

        else:
            management_group = create_group("MANAGEMENT")
            add_button(management_group, "Offer Management", self.usta_offer)
            add_button(management_group, "Stock Management", self.manage_spare_parts)
            add_button(management_group, "Service Center", self.manage_service_center)

            report_group = create_group("REPORTS")
            add_button(report_group, "Customer Feedbacks", self.show_all_feedbacks)

            communication_group = create_group("COMMUNICATION")
            add_button(communication_group, "Send Message", self.send_message)
            add_button(communication_group, "Send Notification", self.create_notification)

            admin_group = create_group("ADMIN")
            add_button(admin_group, "Delete Record", self.del_rep)

        general_group = create_group("GENERAL")
        add_button(general_group, "Device History", self.show_history)
        add_button(general_group, "My Messages", self.show_messages)
        add_button(general_group, "Notifications", self.show_notifications)
        add_button(general_group, "Appointments", self.show_appointments)
        add_button(general_group, "Service Information", self.show_service_centers)
        add_button(general_group, "Settings", self.open_settings)

        ctk.CTkButton(
            self.sidebar,
            text="Log Out",
            height=40,
            corner_radius=14,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.logout
        ).pack(fill="x", padx=14, pady=(8, 16))

    def logout(self):
        self.current_user = None
        self.user_role = None
        self.current_person = None
        self.active_menu = "Home"
        self.tree = None
        self.show_login()

    def show_home_page(self):
        self.active_menu = "Home"
        self.clear_content()
        self.create_header("Home")
        self.create_stats()
        self.create_table()
        self.load_table()

    def show_new_repair_page(self):
        self.active_menu = "New Repair Request"
        self.clear_content()
        self.create_header("New Repair Request")
        self.create_customer_form()

    def create_header(self, page_title=None):
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(20, 8))

        title = page_title if page_title else f"{self.user_role} Panel"

        ctk.CTkLabel(header, text=title, font=("Arial", 26, "bold")).pack(side="left")
        ctk.CTkLabel(header, text=f"Welcome, {self.current_user}", font=("Arial", 14), text_color=self.get_sub_text_color()).pack(side="right")

    def create_stats(self):
        rows = self.db.get_data(self.user_role, self.current_user)
        stats = StatisticsManager.get_summary(rows)

        stats_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=8)

        if self.user_role == "Customer":
            titles = [
                ("My Records", stats["total"]),
                ("Pending", stats["pending"]),
                ("Completed", stats["completed"]),
                ("Paid", stats["paid"])
            ]

        elif self.user_role == "Technician":
            titles = [
                ("Assigned to Me", stats["total"]),
                ("Pending", stats["pending"]),
                ("Completed", stats["completed"]),
                ("Rejected", stats["rejected"])
            ]

        else:
            titles = [
                ("All Records", stats["total"]),
                ("Pending", stats["pending"]),
                ("Completed", stats["completed"]),
                ("Rejected", stats["rejected"]),
                ("Earnings", f"{stats['earnings']} TL")
            ]

        for title, value in titles:
            card = ctk.CTkFrame(stats_frame, corner_radius=16)
            card.pack(side="left", expand=True, fill="x", padx=6)

            ctk.CTkLabel(card, text=title, font=("Arial", 13, "bold")).pack(pady=(14, 4))
            ctk.CTkLabel(card, text=str(value), font=("Arial", 22, "bold")).pack(pady=(0, 14))

    def create_customer_form(self):
        form_card = ctk.CTkFrame(self.content, corner_radius=16)
        form_card.pack(fill="x", padx=22, pady=10)

        ctk.CTkLabel(form_card, text="New Repair Request", font=("Arial", 17, "bold")).grid(
            row=0,
            column=0,
            columnspan=5,
            sticky="w",
            padx=16,
            pady=(14, 8)
        )

        techs = self.db.get_users_by_role("Technician")

        if not techs:
            ctk.CTkLabel(
                form_card,
                text="There is no registered technician in the system. You cannot create a repair request right now.",
                text_color="orange"
            ).grid(row=1, column=0, padx=16, pady=14)
            return

        self.e_dev = ctk.CTkEntry(form_card, placeholder_text="Device Brand/Model", height=34)
        self.e_dev.grid(row=1, column=0, sticky="ew", padx=8, pady=8)

        self.e_serial = ctk.CTkEntry(form_card, placeholder_text="Serial No / IMEI", height=34)
        self.e_serial.grid(row=1, column=1, sticky="ew", padx=8, pady=8)

        self.e_tech = ctk.CTkComboBox(form_card, values=techs, height=34)
        self.e_tech.grid(row=1, column=2, sticky="ew", padx=8, pady=8)
        self.e_tech.set(techs[0])

        self.e_dmg = ctk.CTkEntry(form_card, placeholder_text="Damage Description", height=34)
        self.e_dmg.grid(row=1, column=3, sticky="ew", padx=8, pady=8)

        ctk.CTkButton(
            form_card,
            text="Create Record",
            height=34,
            fg_color=self.primary_color,
            command=self.add_rep
        ).grid(row=1, column=4, sticky="ew", padx=8, pady=8)

        for i in range(5):
            form_card.grid_columnconfigure(i, weight=1)

    def create_table(self):
        table_card = ctk.CTkFrame(self.content, corner_radius=16)
        table_card.pack(fill="both", expand=True, padx=22, pady=(8, 22))

        ctk.CTkLabel(table_card, text="Repair Records", font=("Arial", 17, "bold")).pack(
            anchor="w",
            padx=16,
            pady=(14, 8)
        )

        style = ttk.Style()
        style.theme_use("default")

        if self.settings.theme == "Light":
            bg = "#ffffff"
            fg = "#222222"
            field_bg = "#ffffff"
            heading_bg = self.primary_color
        else:
            bg = "#252525"
            fg = "white"
            field_bg = "#252525"
            heading_bg = self.primary_color

        style.configure(
            "Treeview",
            background=bg,
            foreground=fg,
            fieldbackground=field_bg,
            rowheight=30,
            borderwidth=0
        )

        style.configure(
            "Treeview.Heading",
            background=heading_bg,
            foreground="white",
            font=("Arial", 10, "bold")
        )

        style.map("Treeview", background=[("selected", self.primary_color)])
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        table_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        cols = (
            "ID",
            "Customer",
            "Technician",
            "Device",
            "Serial No",
            "Damage",
            "Status",
            "Price",
            "Time",
            "Payment",
            "Date"
        )

        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)

        y_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )

        for col in cols:
            self.tree.heading(col, text=col)

            if col == "ID":
                self.tree.column(col, width=55, anchor="center")
            elif col == "Damage":
                self.tree.column(col, width=190, anchor="center")
            elif col == "Serial No":
                self.tree.column(col, width=140, anchor="center")
            elif col == "Device":
                self.tree.column(col, width=130, anchor="center")
            elif col == "Status":
                self.tree.column(col, width=130, anchor="center")
            else:
                self.tree.column(col, width=105, anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)