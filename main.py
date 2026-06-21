from ui import TechApp


# Programın başlangıç noktası.
# TechApp nesnesi oluşturulur ve uygulama çalıştırılır.
if __name__ == "__main__":

    # Ana uygulama nesnesi oluşturulur
    app = TechApp()

    # Uygulamanın sürekli çalışmasını sağlayan ana döngü başlatılır
    app.mainloop()