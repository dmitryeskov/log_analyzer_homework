import argparse
import json
import os
import re
import logging
import gzip
from datetime import datetime
from collections import defaultdict
from statistics import median


BASE_CONFIG = {"REPORT_SIZE": 1000, "REPORT_DIR": "./reports", "LOG_DIR": "./log"}


def setup_logging():
    log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_line(line):

    pattern = r'"GET (\S+) HTTP/\d\.\d".*?(\d+\.\d+)$'
    match = re.search(pattern, line)

    if match:
        url = match.group(1)
        request_time = float(match.group(2))
        return url, request_time

    return None, None


def collect_url_stats(log_path):
    total_lines = 0
    parsed_lines = 0
    url_stats = defaultdict(list)

    _, ext = os.path.splitext(log_path)
    open_func = gzip.open if ext == ".gz" else open
    mode = "rt" if ext == ".gz" else "r"

    with open_func(log_path, mode) as f:
        for line in f:
            url, time = parse_line(line)
            if url and time:
                url_stats[url].append(time)
                parsed_lines += 1
            total_lines += 1

    return url_stats, total_lines, parsed_lines


def calculate_statistics(url_stats):

    total_time = sum(sum(times) for times in url_stats.values())
    total_requests = sum(len(times) for times in url_stats.values())

    result = []

    for url, times in url_stats.items():
        count = len(times)
        time_sum = sum(times)
        time_avg = time_sum / count
        time_max = max(times)
        time_med = round(median(sorted(times)), 3)

        time_perc = round((time_sum / total_time) * 100, 2) if total_time > 0 else 0
        count_perc = (
            round((count / total_requests) * 100, 2) if total_requests > 0 else 0
        )

        result.append(
            {
                "url": url,
                "count": count,
                "time_sum": round(time_sum, 3),
                "time_avg": round(time_avg, 3),
                "time_max": round(time_max, 3),
                "time_med": time_med,
                "time_perc": time_perc,
                "count_perc": count_perc,
            }
        )

    result.sort(key=lambda x: x["time_sum"], reverse=True)

    return result


def load_config(config_path):
    try:
        with open(config_path, "r") as file:
            file_config = json.load(file)
            BASE_CONFIG.update(file_config)
    except Exception:
        pass


def search_last_log(log_dir_path):
    latest_date = None
    latest_log = None
    latest_file = None

    for filename in os.listdir(log_dir_path):
        match = re.search(r"nginx-access-ui\.log-(\d{8})(\.gz)?", filename)
        if match:
            date_str = match.group(1)
            try:
                file_date = datetime.strptime(date_str, "%Y%m%d").date()
                if latest_date is None:
                    latest_date = file_date
                    latest_file = filename
                elif file_date > latest_date:
                    latest_date = file_date
                    latest_file = filename

            except ValueError:
                continue

    if latest_file:
        return latest_date, os.path.join(log_dir_path, latest_file)
    else:
        return None, None


def search_exist_report(date, report_dir):

    filename = f"report-{date.strftime('%Y.%m.%d')}.html"
    if filename in os.listdir(report_dir):
        return True
    return False


def generate_report(statistics, log_date, report_dir):

    report_name = f"report-{log_date.strftime("%Y.%m.%d")}.html"
    report_path = os.path.join(report_dir, report_name)

    template_path = os.path.join(os.path.dirname(__file__), "templates", "report.html")

    if not os.path.exists(template_path):
        print(f"[ERROR] Template file not found: {template_path}")
        return False

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        table_json = json.dumps(statistics, ensure_ascii=False)

        report_content = template.replace("$table_json", table_json)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"[INFO] Отчёт успешно создан: {report_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Ошибка при генерации отчёта: {e}")
        return False


def main():
    setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    args = parser.parse_args()

    load_config(args.config)

    logs_dir = os.path.normpath(os.path.join(os.getcwd(), BASE_CONFIG["LOG_DIR"]))
    reports_dir = os.path.normpath(os.path.join(os.getcwd(), BASE_CONFIG["REPORT_DIR"]))

    last_date, last_log = search_last_log(logs_dir)

    if not last_log:
        print(f"[INFO] Нет логов для обработки: {logs_dir}")
        return None

    if search_exist_report(last_date, reports_dir):
        print(f"[INFO] Отчет для лога: {last_log}")
        print(f"[INFO] Уже существует в папке: {reports_dir}")
        return None

    url_stats, total_lines, parsed_lines = collect_url_stats(last_log)

    top_urls_statistics = calculate_statistics(url_stats)[: BASE_CONFIG["REPORT_SIZE"]]

    generate_report(top_urls_statistics, last_date, reports_dir)


if __name__ == "__main__":
    main()
