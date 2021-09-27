# prometheus-scrape-config

## Description

The Prometheus scrape config operator supports the creation of a set of
Prometheus scrape configuration options. Such a set of configuration options
may then be used to override corresponding options set in scrape jobs
forwarded by any scrape target charm. In order to facilitate such overriding
of scrape job configurations, the scrape configuration charm is interposed
between a scrape target and the Prometheus charm.

## Usage

An example of how to use the scrape configuration operator to configure
scrape jobs for a Cassandra charm is shown below.

```sh
$ juju deploy prometheus-k8s      # Deploys Prometheus
$ juju deploy cassandra-k8s       # Deploys Cassandra

# Deploys the new Charm, specifying a custom scrape interval valid only for the
# scrape job forwarded to prometheus-k8s through its relation with this charm
$ juju deploy prometheus-scrape-configuration scrape-cassandra-configuration --config scrape_interval=20s  

# Link cassandra as scrape target, so that Cassandra’s address is used as a
# static_configs in the scrape job
$ juju relate cassandra-k8s scrape-cassandra-configuration  

$ juju relate scrape-cassandra-configuration prometheus-k8s  
```

## Relations

- A `configurable-scrape-jobs` relation with any Charm that uses the
  `MetricsEndpointConsumer` to implement the `prometheus_scrape` interface.
- A `metrics-endpoint` relation with the Prometheus charm.

## OCI Images

This charm does not use any OCI images.

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines 
on enhancements to this charm following best practice guidelines, and
`CONTRIBUTING.md` for developer guidance.
