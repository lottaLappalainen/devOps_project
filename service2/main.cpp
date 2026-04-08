#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <sys/statvfs.h>
#include <sys/socket.h>
#include <unistd.h>

#include <curl/curl.h>

#include <cstring>
#include <ctime>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <iomanip>

std::string iso_utc_now() {
    time_t t = time(nullptr);
    struct tm g;
    gmtime_r(&t, &g);
    char buf[64];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &g);
    return std::string(buf);
}

double get_uptime_hours() {
    std::ifstream f("/proc/uptime");
    if (!f) return 0.0;
    double s = 0;
    f >> s;
    return s / 3600.0;
}

long get_free_mb() {
    struct statvfs st;
    if (statvfs("/", &st) != 0) return 0;
    unsigned long free_bytes = st.f_bavail * st.f_bsize;
    return free_bytes / (1024UL * 1024UL);
}

void post_to_storage(const std::string &record) {
    CURL *curl = curl_easy_init();
    if (!curl) return;

    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: text/plain");
    curl_easy_setopt(curl, CURLOPT_URL, "http://storage:8200/log");
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, record.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 2L);
    curl_easy_perform(curl);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
}

int main() {
    const int port = 8300;
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == -1) { perror("socket"); return 1; }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(port);

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) { perror("bind"); return 1; }
    if (listen(server_fd, 10) < 0) { perror("listen"); return 1; }

    std::cout << "Service2 (C++) listening on port " << port << std::endl;

    while (true) {
        int client = accept(server_fd, nullptr, nullptr);
        if (client < 0) continue;

        char buffer[8192];
        ssize_t r = recv(client, buffer, sizeof(buffer) - 1, 0);
        if (r <= 0) { close(client); continue; }
        buffer[r] = '\0';
        std::string req(buffer);

        if (req.find("GET /status") != std::string::npos) {
            std::ostringstream rec;
            rec << iso_utc_now() << ": uptime " << std::fixed << std::setprecision(2)
                << get_uptime_hours() << " hours, free disk in root: "
                << get_free_mb() << " MBytes";
            std::string record = rec.str();

            post_to_storage(record);

            std::ostringstream body;
            body << record;
            std::string body_s = body.str();

            std::ostringstream resp;
            resp << "HTTP/1.1 200 OK\r\n"
                 << "Content-Type: text/plain\r\n"
                 << "Content-Length: " << body_s.size() << "\r\n"
                 << "Connection: close\r\n\r\n"
                 << body_s;

            std::string resp_s = resp.str();
            send(client, resp_s.c_str(), resp_s.size(), 0);
        } 
     
        else if (req.find("GET /uptime") != std::string::npos) {
            std::ostringstream body;
            body << get_uptime_hours() * 3600; // seconds
            std::string body_s = body.str();

            std::ostringstream resp;
            resp << "HTTP/1.1 200 OK\r\n"
                 << "Content-Type: text/plain\r\n"
                 << "Content-Length: " << body_s.size() << "\r\n"
                 << "Connection: close\r\n\r\n"
                 << body_s;

            std::string resp_s = resp.str();
            send(client, resp_s.c_str(), resp_s.size(), 0);
        }
        else {
            const char *notfound =
                "HTTP/1.1 404 Not Found\r\nContent-Length:0\r\nConnection: close\r\n\r\n";
            send(client, notfound, strlen(notfound), 0);
        }

        close(client);
    }

    close(server_fd);
    return 0;
}
