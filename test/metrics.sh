#example cli syntax for test purposes
#endpoint
az monitor metrics list-definitions --resource /subscriptions/5f08d643-1910-4a38-a7c7-84a39d4f42e0/resourceGroups/sethurg/providers/Microsoft.MachineLearningServices/workspaces/sethucanary/onlineEndpoints/demo-endpoint
az monitor metrics list --metric RequestLatency_P95 --resource /subscriptions/5f08d643-1910-4a38-a7c7-84a39d4f42e0/resourceGroups/sethurg/providers/Microsoft.MachineLearningServices/workspaces/sethucanary/onlineEndpoints/demo-endpoint
az monitor metrics list --metric RequestsPerMinute --filter "deployment eq 'green' and statusCodeClass ne '2xx'" --aggregation Average --interval PT1M --start-time 02/21/2021T21:52:00+00:00 --end-time 02/21/2021T22:00:00+00:00 --resource /subscriptions/5f08d643-1910-4a38-a7c7-84a39d4f42e0/resourceGroups/sethurg/providers/Microsoft.MachineLearningServices/workspaces/sethucanary/onlineEndpoints/demo-endpoint

#deployment
az monitor metrics list-definitions --resource  /subscriptions/5f08d643-1910-4a38-a7c7-84a39d4f42e0/resourceGroups/sethurg/providers/Microsoft.MachineLearningServices/workspaces/sethucanary/onlineEndpoints/demo-endpoint/deployments/blue
az monitor metrics list --metric "MemoryUtilization" --aggregation Average --interval PT1M --start-time 2021-03-21T14:18:00+00:00 --end-time 2021-03-21T14:21:00+00:00 --resource /subscriptions/5f08d643-1910-4a38-a7c7-84a39d4f42e0/resourceGroups/sethurg/providers/Microsoft.MachineLearningServices/workspaces/sethucanary/onlineEndpoints/demo-endpoint/deployments/blue
az monitor metrics list --metric "CPUUtilization" --aggregation Average --interval PT1M --start-time 2021-03-21T14:18:00+00:00 --end-time 2021-03-21T14:21:00+00:00 --resource /subscriptions/5f08d643-1910-4a38-a7c7-84a39d4f42e0/resourceGroups/sethurg/providers/Microsoft.MachineLearningServices/workspaces/sethucanary/onlineEndpoints/demo-endpoint/deployments/blue

az monitor metrics list --metric "MemoryUtilization" --aggregation Average --interval PT1M --start-time 2021-07-16T14:18:00+00:00 --end-time 2021-07-16T14:21:00+00:00 --resource /subscriptions/6560575d-fa06-4e7d-95fb-f962e74efd7a/resourceGroups/saferollout/providers/Microsoft.MachineLearningServices/workspaces/saferollout/onlineEndpoints/gpt-2/deployments/blue


#using validate_metrics script
python -m test.validate_metrics --client_secret --tenant_id "72f988bf-86f1-41af-91ab-2d7cd011db47" --client_id "9aee0ba6-c30b-4c50-ab28-068ba932cd6b" --chart_name "Validate memory within threshold" --chart_save_path "chart-output" --metric MemoryUtilization --aggregation Average --metrics_condition lte --interval PT1M --num_intervals 4 --threshold 30 --resource_id /subscriptions/6560575d-fa06-4e7d-95fb-f962e74efd7a/resourceGroups/saferollout/providers/Microsoft.MachineLearningServices/workspaces/saferollout/onlineEndpoints/gpt-2/deployments/blue