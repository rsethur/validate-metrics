import os
import logging
import json
import re
import argparse
import matplotlib.pyplot as plt
from tabulate import tabulate
from datetime import datetime,timezone, timedelta
from azure.mgmt.monitor import MonitorManagementClient
from azure.identity import DefaultAzureCredential, AzureCliCredential

def cli_auth(subs_id):    
    credentials = AzureCliCredential()
    # create client
    monitor_client = MonitorManagementClient(
        credentials,subs_id)
    return monitor_client

# Use this auth if CLI auth has any issues - not used currently
# auth credintials is the dict containing access token. Refer here for example of the token: https://github.com/marketplace/actions/azure-login
def sp_auth(auth_credentials):
    os.environ["AZURE_TENANT_ID"] = auth_credentials["TENANT_ID"]
    os.environ["AZURE_CLIENT_ID"] = auth_credentials["CLIENT_ID"]
    os.environ["AZURE_CLIENT_SECRET"] = auth_credentials["CLIENT_SECRET"]
    credentials = DefaultAzureCredential()
    # create client
    monitor_client = MonitorManagementClient(
        credentials,
        auth_credentials["SUBS_ID"])
    return monitor_client

def validate_metrics(metric, aggregation, filter, interval, threshold, metrics_condition, resource_id, num_intervals = None, start_time=None, end_time=None, chart_name = None, chart_save_path = "chart-output/", allow_empty_metrics=True):
    #todo: validate resource uri
    # Extract the subs id from the resource id. Sample resource id: "/subscriptions/xxxxxxx-1910-4a38-a7c7-84a39d4f42e0/resourceGroups/my-rg/providers/Microsoft.MachineLearningServices/workspaces/ws/onlineEndpoints/demo-endpoint"
    logging.info(f"Resource id: {resource_id}")
    subs_id = resource_id.split("/")[2]
    
    # if inputs needed for service principal auth is not present, then fallback to cli auth
    if os.environ.get('TENANT_ID') and os.environ.get('CLIENT_ID') and os.environ.get('CLIENT_SECRET'):        
        auth_credentials = {"TENANT_ID":os.environ["TENANT_ID"], "CLIENT_ID": os.environ["CLIENT_ID"], "CLIENT_SECRET": os.environ["CLIENT_SECRET"], "SUBS_ID":subs_id}        
        monitor_client = sp_auth(auth_credentials)
    else:
        logging.info("falling back on cli auth")
        monitor_client = cli_auth(subs_id)
    
    
    logging.info(f"Metric: {metric}, Aggregation: {aggregation}, Interval: {interval}")
    if filter is not None:
        logging.info(f"Filter: {filter}")
    if metrics_condition is not None:
        logging.info(f"Condition: {metrics_condition}")
    if (start_time is None) and (end_time is None):
        logging.info("Taking current time as endtime since no start_time and end_time provided")
        end_time = datetime.now(timezone.utc).replace(microsecond=0)    
        start_time = end_time - calc_duration(interval, num_intervals)
        end_time = end_time.isoformat().replace('+00:00', 'Z')
        start_time = start_time.isoformat().replace('+00:00', 'Z')
    logging.info(f"start_time:{start_time}, endtime: {end_time}")

    metrics_data_list = monitor_client.metrics.list(
        resource_id,
        timespan="{}/{}".format(start_time, end_time),
        interval=interval,
        metricnames=metric,
        aggregation=aggregation,
        filter = filter
    )

    metrics_data = metrics_data_list.value[0]
    if (len(metrics_data.timeseries)==0):
        if allow_empty_metrics is False:
            logging.info("No metrics found - this is not allowed (parameter allow_empty_metrics has been set to False)")
            raise Exception("No values found for metric")
        else:
            logging.info("No metrics found - exiting")
            return
    
    threshold_breached = False
    for metrics_timeseries_data in metrics_data.timeseries:
        metadata_values = ""
        for metadata in metrics_timeseries_data.metadatavalues:
            metadata_values += metadata.value + " "
        logging.info(f"Metadata: {metadata_values}")
        logging.info(f"Threshold: {threshold}")
        display_table = [["Date/time", "Value", "In threshold?"]]
        metrics_value_list_for_plot = []
        for data in metrics_timeseries_data.data:
            #use python reflection to get the value of the aggregation
            attr_name = aggregation.lower()
            value = getattr(data, attr_name)
            metrics_value_list_for_plot.append(value)
            #compare with threshold
            within_threshold_symbol = "\u2713" # ✓
            if is_threshold_breached(value, threshold, metrics_condition):
                logging.debug("{}: {}".format(value, "Threshold breached!"))
                threshold_breached = True
                within_threshold_symbol = "\u2717" # ✗            
            display_table.append([data.time_stamp, value, within_threshold_symbol])
            logging.debug("{} {}: {}".format(data.time_stamp, value, within_threshold_symbol))
    
        logging.info("\n"+tabulate(display_table, headers="firstrow",  tablefmt="grid"))
        if len(metrics_value_list_for_plot)>0:
            plt.figure()
            num_values = len(metrics_value_list_for_plot)
            time_intervals = list(range(0,num_values,1))
            plt.plot(time_intervals, metrics_value_list_for_plot, color="gray")
            plt.scatter(time_intervals, metrics_value_list_for_plot, color = "blue", s=4)
            threshold_line = [threshold] * num_values
            plt.plot(threshold_line, label = "threshold", color = "red", linestyle="--")
            plt.title(chart_name)
            plt.xlabel("Time intervals")
            plt.ylabel("Metric values")
            plt.legend()
            #plt.show()
            if chart_name is not None:
                if not os.path.exists(chart_save_path):
                    os.makedirs(chart_save_path)                
                plt.savefig(os.path.join(chart_save_path, chart_name))
    if threshold_breached:
        raise Exception("Threshold breached!")
    else:
        logging.info("Success: all values within threshold!")
        return 0

def calc_duration(interval, num_intervals):
    # Supported intervals will be in format:
    # e.g. for minutes: PT1M
    # e.g. for hours: PT12H
    # e.g. for day: P1D
    # more examples here: https://docs.microsoft.com/en-us/rest/api/monitor/metricdefinitions/list
    
    if re.match("PT*\d+[MHD]", interval) is None:
        raise Exception("Invalid interval specified")    
    interval_value = int(re.findall("\d+", interval)[0])
    logging.info(f"Unit of interval is {interval[-1]} & interval value is {interval_value} ")
    if interval[-1] == "M":
        duration_timedelta = timedelta(minutes=interval_value * num_intervals)
    elif interval[-1] == "H":
         duration_timedelta = timedelta(hours=interval_value * num_intervals)
    elif interval[-1] == "D":
         duration_timedelta = timedelta(days=interval_value * num_intervals)
    else:
        raise Exception("Invalid interval specified")    
    logging.info(f"duration_timedelta is {duration_timedelta}")
    return duration_timedelta

def is_threshold_breached(metric_value, threshold, metrics_condition):
    if metrics_condition == "lte":
        if metric_value <= threshold:            
            return False
    elif metrics_condition == "gte":
        if metric_value >= threshold:                 
            return False    
    return True

def main():
    def nullable_string(val):
        if not val:
            return None
        return val
    def nullable_int(val):
        if not val:
            return None
        return int(val)
    parser = argparse.ArgumentParser()    
    parser.add_argument('--metric', type=str, required=True, help="name of the metric")
    parser.add_argument('--aggregation', type=str, required=True, help="type of aggregation")
    parser.add_argument('--metrics_condition', type=str, required=True,choices=["lte","gte"], help="condition to compare metrics value and threshold: allowed lte (less than equals) and gte (greater tha equals)")
    parser.add_argument('--start_time', type=nullable_string, required=False, help="date time in ISO 8601 format (default in UTC timezone) e.g: 02-21-2021 21:14:00")
    parser.add_argument('--end_time', type=nullable_string, required=False, help="date time in ISO 8601 format (default in UTC timezone) e.g: 02-21-2021 21:14:00")
    parser.add_argument('--filter', type=nullable_string, required=False, help="Azure monitor chart filter condition. e.g.: deployment eq 'blue' and statusCodeClass ne '2xx'")
    parser.add_argument('--interval', type=str, required=True, default="PT1M",help="interval e.g. PT1M")
    parser.add_argument('--threshold', type=float, required=True, help="threshold value to compare the metric with")
    parser.add_argument('--resource_id', type=str, required=True, help="arm resource id of the resource")
    parser.add_argument('--num_intervals', type=nullable_int, required=False, help="required only when start and end date not provided. then this pulls the metrics for num_intervals time from current time")
    parser.add_argument('--allow_empty_metrics', type=bool, default=True, required=False, help="if False will throw error incase metrics are not available for the given duration")
    parser.add_argument('--chart_name', type=nullable_string, required=False, help="file name for chart to save")
    parser.add_argument('--chart_save_path', type=nullable_string, required=False, help="path to save the chart")
    args = parser.parse_args()
    print(args)
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("azure").setLevel(logging.WARNING)
    validate_metrics(metric=args.metric, aggregation=args.aggregation, filter=args.filter, interval=args.interval, threshold=args.threshold, metrics_condition=args.metrics_condition, resource_id=args.resource_id, num_intervals=args.num_intervals, start_time=args.start_time, end_time=args.end_time, chart_name=args.chart_name,chart_save_path=args.chart_save_path, allow_empty_metrics=args.allow_empty_metrics)

if __name__ == '__main__':
    main()