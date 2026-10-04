# Product Installation and Local Runtime

Use for new products, selected local-installation options, or changed packaging/startup/deployment behavior. Ordinary changes reuse an adequate existing path and do not trigger unrelated container work or install checks. This concerns the product, not installation of Vibe or its specialists.

## Head-owned selection

Choose the simplest reproducible installation/startup path compatible with the product, target environment and approved scope. Reuse adequate existing packaging or hosting. Project size alone does not require Docker, distributed services or a cluster.

| Product / target | Installation decision |
|---|---|
| Self-hosted web app/API with a database or other required services | Prefer Docker Compose when the target supports containers and it reduces manual setup or environment drift. Include only services the product actually needs. |
| Suitable server product to run on the user's computer | Offer Docker/Compose as a local installation option for trying or using the actual software. When requested or selected, deliver that route as an accepted product outcome, even if production uses another deployment method. |
| Static site or simple CLI | Keep the simplest adequate native or existing hosting path. Add a container option only for an actual requirement. |
| WordPress plugin | Deliver the exact installable plugin ZIP. Compose may provide a disposable WordPress/database environment for local use or testing; it does not replace the plugin artifact or install/upgrade evidence. |
| Desktop or mobile application | Deliver the platform's native installer/package. Containerize a supporting backend only when useful; a backend container is not installation of the client application. |

Docker provides the container runtime; Compose coordinates the selected services, networks and storage. They must be available on the target host. Check platform/architecture compatibility and relevant resource, download or external-service prerequisites before promising local execution. Containerization does not establish offline operation or production readiness.

## Fit the existing lifecycle

| Stage | Head responsibility |
|---|---|
| Plan | Select the supported installation targets and method. Reuse existing acceptance criteria or add the requested local-startup outcome; retain material decisions in the existing plan/contract when required. |
| Build | Provide the selected packaging/configuration and a short user-facing run guide. Create a Dockerfile only when building a product image is necessary; use a Compose file only for the chosen route. |
| Verify | Execute the documented path from a clean disposable state, verify service readiness and one primary user workflow. For stateful products, verify required data survives a stop/start or container recreation. Reuse sufficient evidence and add checks only for changed failure modes. |
| Ship | Deliver the tested revision/artifact with clear start/access/stop and update instructions, actual verification results and relevant recovery steps. Source, local execution and production deployment are separate claims. |

When local installability is required, keep it in the existing acceptance/receipt/handoff route. A passing build, valid Compose configuration or running container alone cannot satisfy it. Missing runtime access or a failed required installation check leaves that outcome unverified/blocked; unrelated passing checks cannot substitute.

## Selected Docker/Compose route

- Provide a runnable image or reproducible build context, the necessary Compose configuration, and a safe configuration example. Document working directory, prerequisites, required secrets/settings, startup command and the actual URL or CLI entrypoint. Do not require developer-only host runtimes merely to use the product when they run inside its containers.
- Make prerequisite services ready before consumers need them, using meaningful health/readiness checks or bounded application retries as appropriate. Set a bounded startup check and expose useful errors/logs rather than leaving the user waiting indefinitely. See [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/).
- Keep user data in appropriate persistent storage. Explain where it lives and separate normal stop/update from destructive reset/removal. A user's trial environment must not silently reuse production credentials or data.
- For local-only use, bind published ports to loopback by default, expose only required endpoints, and keep database/internal services private unless access is explicitly needed. Do not ship real secrets, known shared login credentials or unnecessary privileged/host-wide mounts. See [Docker port publishing](https://docs.docker.com/engine/network/port-publishing/).
- Document only supported host platforms and tested limitations. State any necessary network downloads or external APIs; make a claimed offline route an explicit acceptance outcome. Obtain existing authorization before installing Docker or changing host virtualization/network settings.

Example acceptance: from the delivered package and documented settings, the user starts the app locally, opens its entrypoint and completes the core workflow; after a non-destructive restart, required saved data remains available. Use the actual product's outcome, not a fixed universal test suite.

Production configuration must match its own target and controls. Local development mounts, sample settings and successful localhost execution are not evidence that the same configuration is ready for public deployment. Compose can suit a single-host deployment; availability and multi-host scaling require their own justified architecture decision.

Record the delivered revision/artifact, selected image identity, relevant configuration/platform and observed result using existing engineering evidence. Keep generated logs/reports outside product source; necessary Docker/Compose files and product run instructions belong in the product repository.
