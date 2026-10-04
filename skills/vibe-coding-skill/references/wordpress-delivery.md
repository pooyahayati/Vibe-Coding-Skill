# WordPress Delivery Workflow

Use this reference only when the WordPress capability pack is active and the task includes plugin creation, release, distribution, installation/upgrade behavior, or a delivery artifact.

The goal is an installable plugin artifact with evidence from that exact artifact, not merely a source tree that appears correct.

For a selected local Docker/Compose option, apply `references/product-installation-and-runtime.md`: provide or reuse a suitable WordPress/database environment, install the exact plugin ZIP and exercise its requested behavior. Containers supply the environment; the plugin deliverable and install/upgrade requirements remain unchanged.

## Stage contract

| Stage | Required result |
|---|---|
| Discovery | Decide whether the need is best met by existing configuration/capability, extending an existing plugin, or creating a new plugin. |
| Bootstrap | Confirm plugin slug/name, main plugin header, embedded version, minimum WordPress/PHP support, and required platform/plugin dependencies. |
| Implementation | Use public WordPress APIs/hooks, namespace/prefix plugin-owned symbols, and load assets only on relevant screens/requests. |
| Security | Mutations require authorization/capability checks plus request-intent protection when applicable; validate/sanitize input and escape output at the correct boundary. A nonce is not authorization. |
| Data/lifecycle | Fresh install, upgrade, deactivation, and uninstall behavior must match the documented data-retention policy. Deactivation and uninstall are different events. |
| UI | Verify actual behavior, internationalization, and RTL when the supported audience requires it. |
| WooCommerce | When relevant, use public CRUD/APIs and verify the affected HPOS and Cart/Checkout Blocks compatibility surfaces rather than assuming posts-based storage or classic checkout. |
| Delivery | Build one installable ZIP, verify its embedded version/shape, and run install/upgrade checks against that exact ZIP. |

## Prepared distribution source

Run project-specific build steps first. The packaging helper intentionally does not infer how a plugin builds JavaScript, CSS, Composer assets, generated files, or vendor dependencies.

Create a prepared distribution directory containing exactly the files intended for the plugin package, then package it:

```bash
python scripts/wordpress_artifact.py package \
  --source-root <prepared-plugin-dir> \
  --output <plugin.zip> \
  --slug <plugin-slug> \
  --json
```

The helper creates a deterministic ZIP with one top-level plugin directory and records the artifact SHA-256.

It rejects symlinks and malformed plugin package structure. The source must contain one root-level PHP main plugin file with a `Plugin Name` header and an embedded `Version`.

## Artifact verification

Verify the exact artifact before installation:

```bash
python scripts/wordpress_artifact.py verify \
  --artifact <plugin.zip> \
  --expected-slug <plugin-slug> \
  --expected-version <release-version> \
  --json

python scripts/wordpress_artifact.py install-smoke \
  --artifact <plugin.zip> \
  --json
```

`install-smoke` safely extracts the ZIP into a temporary `wp-content/plugins/` shape and confirms the installed main plugin header/version. This is packaging evidence, not a substitute for a real WordPress runtime test.

## Real WordPress install and upgrade

For a delivery/release task, use a disposable or dedicated WordPress test environment and run the same artifact through WP-CLI:

```bash
python scripts/wordpress_artifact.py runtime-check \
  --artifact <plugin.zip> \
  --wordpress-root <wordpress-root> \
  --json
```

For an upgrade path, provide the previously released artifact:

```bash
python scripts/wordpress_artifact.py runtime-check \
  --previous-artifact <previous-release.zip> \
  --artifact <candidate-release.zip> \
  --wordpress-root <wordpress-root> \
  --json
```

The runtime check:

- installs/activates the exact ZIP path;
- confirms the installed version equals the ZIP header;
- for upgrades, installs the previous ZIP first and then the candidate ZIP;
- deactivates/reactivates the plugin;
- records SHA-256 for the tested artifact(s).

Do not claim install/upgrade validation from source-only tests.

The helper records the initial plugin list. `fresh_plugin_install_checked` only means that the plugin was absent before this install and no previous artifact was supplied. Existing options/tables may remain, so `fresh_install_checked` and `data_freshness_verified` stay false. Establish a clean database/site independently before claiming a full fresh installation. `upgrade_checked` proves the previous-to-candidate install sequence, not preservation of project data; add a focused seeded-data check when the upgrade can affect stored data.

## Uninstall and retention

Uninstall may delete plugin-owned data and therefore must not be inferred from deactivation behavior.

The helper will exercise uninstall only when both flags are supplied:

```text
--exercise-uninstall --disposable-environment
```

This only verifies that uninstall completes in a disposable environment. Project-specific tests must separately verify the promised retention/deletion semantics for options, tables, uploads, scheduled events, and other owned data.

Never delete user data merely because a plugin is deactivated.

## WordPress security specifics

For state-changing operations:

- capability/authorization checks decide whether the actor is allowed;
- nonces/request-intent checks help protect against unintended requests;
- input validation/sanitization enforces data semantics;
- output escaping belongs at the output context;
- SQL uses WordPress APIs or prepared queries.

A valid nonce without sufficient capability is not authorization.

## Plugin Check and runtime behavior

Use the official Plugin Check tool proportionately when release scope, WordPress.org compatibility, or the changed surface justifies it.

Plugin Check is standards/static evidence. It does not replace:

- installing the release ZIP;
- activating the feature;
- running the relevant user workflow;
- upgrade/lifecycle verification;
- project-specific security or data-integrity tests.

Record the Plugin Check version/result when it is used.

## WooCommerce delivery

When WooCommerce behavior is affected:

- declare/check supported WordPress and WooCommerce ranges;
- use public WooCommerce CRUD and extension APIs;
- test HPOS compatibility when order storage is involved;
- test Cart/Checkout Blocks only when the extension touches those surfaces;
- verify order/payment state transitions, retries, idempotency, and rollback/recovery according to risk.

Do not add WooCommerce compatibility ceremony to a plugin that does not use WooCommerce.

## Composer / Packagist fallback

The bundled dependency guard does not currently provide a Composer/Packagist adapter.

For PHP Composer dependencies, do not pretend the generic dependency guard verified them. Use native/official evidence first:

- inspect `composer.json` and the committed `composer.lock`;
- verify the package/version on Packagist or the package's official distribution/source;
- run `composer validate`;
- run `composer audit` for the locked dependency set when available;
- review license, provenance/source, maintenance, and necessity using the same risk principles as other dependencies.

Add a dedicated Packagist adapter only when the repeated workflow justifies maintaining it.

## Delivery evidence

A WordPress release is ready only when evidence appropriate to the change includes:

- artifact path and SHA-256;
- plugin slug and embedded version;
- package/install smoke result;
- real WordPress install result for delivery scope;
- upgrade result when upgrading an existing released plugin;
- relevant lifecycle/data-retention evidence;
- relevant feature/security/integration tests;
- WooCommerce compatibility evidence when applicable;
- Plugin Check evidence when justified.

The exact artifact tested should be the artifact delivered.
