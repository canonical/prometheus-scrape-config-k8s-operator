## Deployment scenarios
The `scrape-config` charm can be used for example to set different scrape
intervals for different jobs. The adjusted scrape job can then be forwarded to
grafana agent:

```mermaid
graph LR

subgraph K8s model
postgresql --- sc1[scrape-config]
sc1 --- ga[grafana-agent]

st[scrape-target] --- sc2[scrape-config]
sc2 --- ga
end

ga --- prometheus

subgraph O11y k8s model
prometheus
end

style sc1 stroke-width:4px
style sc2 stroke-width:4px
```

Both scrape-config and scrape-target are workloadless charms, so they can be
deployed in VM models. Note that cross-model scrape is discouraged, and that
you may need to take special care to have the scrape target reachable by
prometheus.

```mermaid
graph LR

subgraph LXD model
nrpe --- cos-proxy --- sc[scrape-config]
st[scrape-target] --- sc[scrape-config]

end

sc --- prometheus

subgraph O11y k8s model
prometheus
end

style sc stroke-width:4px
```

Another option is to deploy scrape-config inside the Observability model
itself. This is usually not recommended for production deployments.

```mermaid
graph

subgraph O11y k8s model
scrape-target --- scrape-config --- prometheus
end

style scrape-config stroke-width:4px
```


## `scrape_configs` manipulation

Generally, the prometheus config file ([example][prom-config-example])
has the following form:

| Section          | Provided by                                             |
|------------------|---------------------------------------------------------|
| `global`         | promethehus                                             |
| `rule_files`     | rules from upstream charms; re-structured by prometheus |
| `alerting`       | alertmanager                                            |
| `tracing`        | (not yet implemented)                                   |
| `scrape_configs` | upstream charms, prometheus-scrape-config               |

The `scrape_configs` section is made up of:

| Subsection        | Provided by                                                              |
|-------------------|--------------------------------------------------------------------------|
| `job_name`        | upstream charm (optional); topology-prefixed and deduped (consumer side) |
| `static_configs`  | upstream charm                                                           |
| `metrics_path`    | upstream charm                                                           |
| `relabel_configs` | upstream charm (optional); topology-adjusted (consumer side)             |
| `scrape_interval` | upstream charm, prometheus-scrape-config                                 |
| etc.              | upstream charm, prometheus-scrape-config                                 |

This charm updates some values in the `scrape_configs` section.

The `static_configs` section is made up of:

| Sub-subsection | Provided by                                              |
|----------------|----------------------------------------------------------|
| `targets`      | upstream charm (star notation expanded on consumer side) |
| `labels`       | upstream charm                                           |


[prom-config-example]: https://github.com/prometheus/prometheus/blob/release-2.37/config/testdata/conf.good.yml
