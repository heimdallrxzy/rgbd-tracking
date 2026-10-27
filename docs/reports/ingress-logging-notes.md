# normal1 ingress evaluation folders

- [The final timing report](ingress-timing.md) uses the rebuilt asynchronous writer and is the report to use for conclusions.
- `normal1_ingress_20261021_103207` is a preliminary run with a ROS subscription-discovery startup race. Do not use it for frame-loss comparisons.
- `normal1_ingress_20261021_103921` waited for both subscriptions, but was captured before the final logger lock fix. Retained for audit; use the final folder above instead.

The raw run folders are not included in this public package.
