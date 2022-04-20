import argparse
import json
import os
import re

parser = argparse.ArgumentParser(description="Process logs")
parser.add_argument("-l", dest="log", action="store", help="Path to logfile or logdir")

args = parser.parse_args()


def update_ips_reqs_counter(ips_reqs_counter, ip):
    is_should_update_existed_counter = ip in ips_reqs_counter
    if is_should_update_existed_counter:
        ips_reqs_counter[ip]["REQUESTS_COUNT"] += 1
    else:
        # init new counter
        ips_reqs_counter[ip] = {
            "REQUESTS_COUNT": 1
        }


def get_param_from_log_line(line, param_name):
    def get_method():
        return re.search(r"\] \"(POST|GET|PUT|DELETE|HEAD|OPTIONS)", line)

    def get_ip():
        return re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", line).group()

    def get_date():
        return re.search(r"\[\d.*?\]", line)

    def get_url():
        return re.search(r"\"http.*?\"", line)

    parsers = {
        "method": get_method,
        "ip": get_ip,
        "date": get_date,
        "url": get_url
    }

    line_parser = parsers[param_name]

    return line_parser()


def parse_log_file(logs):
    dict_ip = {
        "TOTAL": 0,
        "METHOD": {"GET": 0, "POST": 0, "PUT": 0, "DELETE": 0, "HEAD": 0, "OPTIONS": 0}
    }
    ips_reqs_counter = {}

    list_ip_duration = []

    with open(logs) as logfile:

        for line in logfile:
            # method = re.search(r"\] \"(POST|GET|PUT|DELETE|HEAD|OPTIONS)", line)
            # ip = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", line).group()
            # duration = int(line.split()[-1])
            # date = re.search(r"\[\d.*?\]", line)
            # url = re.search(r"\"http.*?\"", line)

            method = get_param_from_log_line(line, 'method')
            ip = get_param_from_log_line(line, 'ip')
            duration = int(line.split()[-1])
            date = get_param_from_log_line(line, 'date')
            url = get_param_from_log_line(line, 'url')

            dict_ip["TOTAL"] += 1

            if method is not None:

                dict_ip["METHOD"][method.group(1)] += 1

                update_ips_reqs_counter(ips_reqs_counter, ip)

                dict_t = {"IP": ip,
                          "METHOD": method.group(1),
                          "URL": "-",
                          "DATE": date.group(0).split(" ")[0].lstrip("["),
                          "DURATION": duration
                          }

                if url is not None:
                    dict_t["URL"] = url.group(0).strip("\"")

                list_ip_duration.append(dict_t)

        top3_req = dict(sorted(ips_reqs_counter.items(), key=lambda x: x[1]["REQUESTS_COUNT"], reverse=True)[0:3])
        top3_slw = sorted(list_ip_duration, key=lambda x: x["DURATION"], reverse=True)[0:3]

        result = {
            "total_requests": dict_ip["TOTAL"],
            "total_stat": dict_ip["METHOD"],
            "top3_ip_requests": top3_req,
            "top3_slowly_requests": top3_slw
        }

        with open(f"{logs}.json", "w", encoding="utf-8") as file:
            result = json.dumps(result, indent=4)
            file.write(result)
            print(f"\n===== LOG FILE: {logs} =====\n {result}")


if args.log is not None:
    if os.path.isfile(args.log):
        parse_log_file(logs=args.log)

    elif os.path.isdir(args.log):
        for file in os.listdir(args.log):
            if file.endswith(".log"):
                path_to_logfile = os.path.join(args.log, file)
                parse_log_file(logs=path_to_logfile)

    else:
        print("ERROR: Incorrect path to log file or directory")
