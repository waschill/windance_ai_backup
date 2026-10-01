# First-admin guard verification — October 1, 2026

The installed lab auths.py (SHA2564be0ed8e69bba85c0392fdddf006efe5592c322a4973c669120a0a0c3c2424c7) explicitly exempts the first administrator from ui.enable_signup. Therefore changing ENABLE_SIGNUP alone is not an effective containment plan for the currently empty lab.

Four checks of the exact AST-extracted leading signup guard passed with synthetic Users and Config stubs. They establish: signup=false still permits first-admin registration when login is enabled; login=false plus initial-admin-signup=false blocks it; the initial-admin override can permit it even with login disabled; and signup=false blocks subsequent registration. No actual registration code, database, network or application startup ran. This validates the guard only, not an end-to-end configuration deployment.

The official [first-run guidance](https://docs.openwebui.com/security/accepted-risks/first-run-bootstrap-window/) recommends completing setup through a private network, VPN or local port before exposure, or explicitly provisioning the administrator at startup. The installed code agrees that the first account becomes administrator. Do not generate or record a password in shared context, create an administrator implicitly, or infer that the current trusted LAN is publicly exposed.

Docker inspect found no Compose ownership labels for this lab. Its one published binding is192.168.36.20:3001 and it retains a named data volume. A change must preserve the full existing private container definition, volume, runtime settings and dependencies; recreating it from a partial guessed docker command is not an acceptable recovery plan.

Recommended next implementation: establish intended admin ownership and restrict bootstrap access during enrollment, using supported configuration. Alternatively, an intentionally inaccessible empty lab requires both the login-form and initial-admin guard settings to be effective, with persisted settings accounted for and recovery access documented. No option was deployed here. Production WebUI, model routes, staff services and SAM remain unchanged. No new account, credential or paid commitment was created.
