FROM debian:bullseye-slim

# Instalacja telnet i xinetd
RUN apt-get update && apt-get install -y \
    telnetd \
    xinetd \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Kopiujemy flagę
COPY flag.txt /root/flag.txt

# Kopiujemy skrypt startowy
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Konfiguracja xinetd dla telnet
RUN echo "service telnet" > /etc/xinetd.d/telnet && \
    echo "{" >> /etc/xinetd.d/telnet && \
    echo "  disable         = no" >> /etc/xinetd.d/telnet && \
    echo "  socket_type     = stream" >> /etc/xinetd.d/telnet && \
    echo "  protocol        = tcp" >> /etc/xinetd.d/telnet && \
    echo "  wait            = no" >> /etc/xinetd.d/telnet && \
    echo "  user            = root" >> /etc/xinetd.d/telnet && \
    echo "  server          = /usr/sbin/in.telnetd" >> /etc/xinetd.d/telnet && \
    echo "  server_args     = -L /bin/login" >> /etc/xinetd.d/telnet && \
    echo "}" >> /etc/xinetd.d/telnet

# Usuwamy hasło roota (kluczowa część!)
RUN passwd -d root

# Tworzymy dodatkowych użytkowników dla zmyłki
RUN useradd -m -s /bin/bash adam && echo "adam:adam123" | chpasswd
RUN useradd -m -s /bin/bash kasia && echo "kasia:kasia456" | chpasswd
RUN useradd -m -s /bin/bash guest && echo "guest:guest" | chpasswd

# Dodajemy fałszywą flagę dla zmyłki
RUN echo "FLAG{this_is_a_fake_flag}" > /home/guest/fake_flag.txt
RUN echo "FLAG{try_harder}" > /home/adam/secret.txt

# Dodajemy dodatkowe pliki do zbadania
RUN echo "To nie jest flaga, szukaj dalej!" > /var/log/messages

# Otwieramy port
EXPOSE 23

# Uruchamiamy xinetd
CMD ["/start.sh"]