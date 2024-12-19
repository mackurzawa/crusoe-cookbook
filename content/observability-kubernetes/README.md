# Integrating observability stack into your Kubernetes cluster

This cookbook outlines the process of setting up an observability stack in your Kubernetes cluster, including Prometheus, Grafana, and exporters for node and GPU metrics.

## Resource provisioning

The simplest way to provision a cluster on Crusoe is to use our [RKE2 Terraform](https://github.com/crusoecloud/crusoe-ml-rke2). Complete the steps described in that repository and make sure you have access to the cluster with `kubectl`.

## Installing Prometheus Operator
The prometheus Operator simplifies the deployment and management of Prometheus instances in Kubernetes.

### Steps
#### 1. Add Helm repository
```bash
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
$ helm repo update
```
#### 2. Install Prometheus Operator

Create a file called `prometheus-values.yaml` with contents:
```yaml
additionalScrapeConfigs:
- job_name: gpu-metrics
  scrape_interval: 1s
  metrics_path: /metrics
  scheme: http
  kubernetes_sd_configs:
  - role: endpoints
    namespaces:
    names:
    - gpu-operator
  relabel_configs:
  - source_labels: [__meta_kubernetes_pod_node_name]
    action: replace
    target_label: kubernetes_node
```

```bash
$ helm install prometheus-operator prometheus-community/kube-prometheus-stack \
    --namespace monitoring -f prometheus-values.yaml --create-namespace
```
#### 3. Verify the installation
```bash
$ kubectl --namespace monitoring get pods \
    -l "release=prometheus-operator"
```
Ensure all pods are working and in healthy state.

## Installing and configuring the NVidia GPU Operator with DCGM exporter
### Steps
#### 1. Install the GPU Operator using Helm:
```bash
$ helm repo add nvidia https://nvidia.github.io/gpu-operator
$ helm repo update
$ helm install --wait --generate-name nvidia/gpu-operator --set serviceMonitor.enabled=true --namespace gpu-operator --create-namespace
```
This command adds the NVIDIA Helm repository, updates the repositories, and installs the GPU Operator in the `gpu-operator` namespace. The `--wait` flag ensures that Helm waits for the operator's deployment to be completed and the `--create-namespace` flag creates the namespace if it doesn't exist.
#### 2. Verify the GPU Operator and driver Installation:
```bash
$ kubectl get pods -n gpu-operator
```
Make sure all pods are either in helthy state or have completed running.

## Installing and configuring Grafana
Grafana is a visualization tool that can be used to create dashboards for monitoring your Kubernetes cluster and applications, including GPU metrics collected by dcgm-exporter. If you installed Prometheus using the kube-prometheus-stack Helm chart, Grafana is already installed as part of that package. We'll now cover accessing Grafana and configuring data sources.

## Steps:
#### 1. Access Grafana:

If you used the `kube-prometheus-stack` Helm chart, you can access Grafana using port-forwarding:

```bash
$ kubectl -n monitoring port-forward svc/prometheus-operator-grafana 3000:80
```

Now, open your web browser and navigate to `http://localhost:3000`.

Alternatively, if you have an ingress controller setup, you can create an Ingress rule to expose Grafana. Here's an example Ingress configuration:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
    name: grafana-ingress
    namespace: monitoring
    annotations:
    # Add any necessary annotations for your ingress controller
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
    rules:
    - host: grafana.your-domain.com
    http:
        paths:
        - path: /
        pathType: Prefix
        backend:
            service:
            name: prometheus-operator-grafana
            port:
                number: 80
```

#### 2. Login to Grafana
The default credentials for Grafana when installed with the kube-prometheus-stack Helm chart are:
- Username: admin
- Password: You can get the password by running the following command:
```bash
$ kubectl -n monitoring get secret prometheus-operator-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
```
You will be prompted to change the password after the first login.

#### 3. Configure Prometheus as a data source
If you installed Grafana using the `kube-prometheus-stack` Helm chart, the Prometheus data source should already be configured automatically. However, you can verify or manually add it if needed.

*   Go to *Connections* > *Data Sources*.
*   You should see a data source named `Prometheus` already configured.
*   If not, click *Add data source*, select *Prometheus*.
*   Enter the following details:
    *   **URL:**  `http://prometheus-operator-prometheus.monitoring.svc.cluster.local:9090`
    *   **Name:** `Prometheus` (or any other name you prefer)
*   Click *Save & Test*. You should see a success message if the data source is configured correctly.

## Grafana dashboards
Grafana dashboards provide a visual representation of your cluster and application metrics. You can create custom dashboards or import pre-built ones. Here are some recommended dashboards for GPU observability:
- *Node Exporter Dashboard*: For general node metrics, including CPU, memory, and disk utilization, you can use the Node Exporter dashboard.
- *NVIDIA DCGM Exporter Dashboard*: The dcgm-exporter project provides a recommended Grafana dashboard that you can import. You can find the JSON definition in the dcgm-exporter GitHub repository under grafana-dashboards/dcgm-exporter-dashboard.json or download it directly from a running dcgm-exporter instance at [/dashboards/dcgm-exporter-dashboard.json](https://github.com/NVIDIA/dcgm-exporter/blob/main/grafana/dcgm-exporter-dashboard.json).

To import this dashboard:
- download the JSON file
- in Grafana, go to Dashboard (+) > New > Import
- upload the JSON file or paste the JSON content
- select the Prometheus data source you configured earlier
- click Import
- this dashboard provides comprehensive metrics about your GPUs, including utilization, temperature, power usage, memory usage, and more

## Running an example ML workflow

To demonstrate the observability stack in action, we'll deploy a simple machine learning workload using TensorFlow and MNIST dataset. This example will allow you to observe GPU resource utilization in Grafana. This assumes you have the `nvidia-device-plugin` running, which is typically installed as part of the GPU Operator.

### Steps

1. **Deploy the TensorFlow MNIST example:**

Use the following YAML configuration to deploy a TensorFlow training job:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: tensorflow-mnist
spec:
  containers:
  - name: tensorflow-mnist
    image: tensorflow/tensorflow:latest-gpu  # Use a TensorFlow image with GPU support
    resources:
      limits:
        nvidia.com/gpu: 1 # Request one GPU
    command: ["python", "/tensorflow/tensorflow/examples/tutorials/mnist/mnist_with_summaries.py"]
```

Save this configuration as `tensorflow-mnist.yaml` and apply it to your cluster:

```bash
kubectl apply -f tensorflow-mnist.yaml
```

2. **Observe GPU metrics in Grafana:**

*   Open your Grafana dashboard (e.g., `http://localhost:3000` if using port-forwarding).
*   Navigate to the NVIDIA DCGM Exporter dashboard you imported earlier.
*   You should now see GPU metrics being populated, reflecting the resource utilization of the TensorFlow training job. You should see increases in GPU utilization, memory usage, and potentially temperature.

1. **(Optional) Scale the workload:**

To see a more significant impact on GPU metrics, you can scale the TensorFlow deployment. This will launch multiple pods, each consuming GPU resources.

```bash
kubectl scale pod tensorflow-mnist --replicas=2
```

Observe the changes in your Grafana dashboards as the workload scales.

4. **(Optional) Stress test the GPUs:**

For a more intensive test, consider using a dedicated GPU benchmark tool like `nvidia-smi` inside your pod. This allows you to push the GPUs to their limits and observe the corresponding metrics in Grafana. An example command within the container could be:

```bash
nvidia-smi -lms 100  # Loop nvidia-smi every 100 milliseconds
```

Remember to adjust the resource requests and limits in your pod definition to match the desired load.

5. **Clean up:**
After you're finished observing the metrics, delete the TensorFlow pod to release the GPU resources:

```bash
kubectl delete pod tensorflow-mnist
```

This example demonstrates how to deploy a simple ML workload and monitor its GPU usage using the observability stack. You can adapt this approach to monitor more complex ML applications and gain insights into their resource consumption and performance. Remember to tailor the resource requests and limits in your pod definitions to match the specific requirements of your workloads.
