# Model Monitoring

Operational monitoring has two distinct signals. Drift monitoring works without labels and
detects changes in input and prediction distributions. Performance monitoring requires delayed
labels and computes the same classification metrics used during evaluation.

Alerts are local JSON and Markdown artifacts. In a future cloud deployment, the same result
objects can be emitted as structured logs and converted into Cloud Monitoring metrics.

