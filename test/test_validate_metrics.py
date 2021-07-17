import unittest
import logging
import os
import vcr
from metrics.validate_metrics import validate_metrics

class TestValidateMetricsWithinThreshold(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.deployment_resource_id = "/subscriptions/5f08d643-1910-4a38-a7c7-84a39d4f42e0/resourceGroups/sethurg/providers/Microsoft.MachineLearningServices/workspaces/sethucanary/onlineEndpoints/demo-endpoint/deployments/blue"
        cls.endpt_resource_id = "/subscriptions/5f08d643-1910-4a38-a7c7-84a39d4f42e0/resourceGroups/sethurg/providers/Microsoft.MachineLearningServices/workspaces/sethucanary/onlineEndpoints/demo-endpoint"

    @vcr.use_cassette("test/metrics_vcr/test_simple_metric_memory_within_threshold.yaml")
    def test_simple_metric_memory_within_threshold(self):        
        ret = validate_metrics(metric="MemoryUtilization", aggregation="Average", filter=None, interval="PT1M", threshold=10, metrics_condition="lte", start_time="02-21-2021 21:52:00",end_time="02-21-2021 22:30:00", resource_id=self.deployment_resource_id)
        self.assertEqual(ret, 0)
        ret = validate_metrics(metric="MemoryUtilization", aggregation="Average", filter=None, interval="PT1M", threshold=1, metrics_condition="gte", start_time="02-21-2021 21:52:00",end_time="02-21-2021 22:30:00", resource_id=self.deployment_resource_id)
        self.assertEqual(ret, 0)

    @vcr.use_cassette("test/metrics_vcr/test_simple_metric_memory_within_threshold_fail.yaml")
    def test_simple_metric_memory_within_threshold_fail(self):        
        with self.assertRaises(Exception):
            validate_metrics(chart_name="Validate memory within threshold", metric="MemoryUtilization", aggregation="Average", filter=None, interval="PT1M", threshold=1, metrics_condition="lte", start_time="02-21-2021 21:52:00",end_time="02-21-2021 22:30:00", resource_id=self.deployment_resource_id)
        

    @vcr.use_cassette("test/metrics_vcr/test_simple_metric_latency_within_threshold.yaml")
    def test_simple_metric_latency_within_threshold(self):        
        ret = validate_metrics(chart_name="Validate latency within threshold", metric="RequestLatency_P90", aggregation="Average", filter=None, interval="PT1M", threshold=100, metrics_condition="lte", resource_id=self.endpt_resource_id, start_time="02-21-2021 21:52:00",end_time="02-21-2021 22:30:00",)
        self.assertEqual(ret, 0)
    
    @vcr.use_cassette("test/metrics_vcr/test_metric_with_filtering_and_multiple_dimensions.yaml")
    def test_metric_with_filtering_and_multiple_dimensions(self):        
        with self.assertRaises(Exception):
            validate_metrics(metric="RequestsPerMinute", aggregation="Average", metrics_condition="lte", start_time="02-21-2021 21:14:00",end_time="02-21-2021 21:39:00", filter="deployment eq 'blue' and statusCodeClass ne '2xx'", interval="PT1M", threshold=1000, resource_id=self.endpt_resource_id)
        
    
    @unittest.skip("this one will not use caching - will pull live data")
    def test_simple_metric_memory_within_threshold_no_time_bounds(self):
        ret = validate_metrics(metric="MemoryUtilization", aggregation="Average", filter=None, interval="PT1M", num_intervals=4, threshold=7, metrics_condition="lte", resource_id=self.deployment_resource_id)
        self.assertEqual(ret, 0)
    
    @unittest.skip("this one will not use caching - will pull live data")
    def test_cli_with_start_and_end_date(self):                
        cmd = f"python -m test.validate_metrics --metric RequestsPerMinute --aggregation Average --metrics_condition lte --start_time \"02-21-2021 21:14:00\" --end_time \"02-21-2021 21:39:00\" --filter \"deployment eq 'blue' and statusCodeClass ne '2xx'\" --interval PT1M --threshold 1000 --resource_id \"{self.endpt_resource_id}\""
        ret = os.system(cmd)
        self.assertEqual(ret, 1)
    
    @unittest.skip("this one will not use caching - will pull live data")
    def test_cli_with_with_live_data(self):                
        cmd = f"python -m test.validate_metrics --metric MemoryUtilization --aggregation Average --metrics_condition lte --interval PT1M --num_intervals 10 --threshold 7 --chart_name mychart --chart_save_path chart-output --resource_id \"{self.deployment_resource_id}\""
        ret = os.system(cmd)
        self.assertEqual(ret, 0)
            
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("vcr").setLevel(logging.WARNING)
    unittest.main()